from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Conta, Categoria
from django.contrib import messages
from django.contrib.messages import constants
from .utils import calcula_total, calcula_equilibrio_financeiro
from extrato.models import Valores
from django.db.models import Sum
from datetime import datetime
from contas.models import ContaPagar, ContaPaga

# Create your views here.
def home(request):
    contas = Conta.objects.all()
    contas_pagar = ContaPagar.objects.all()
    valores = Valores.objects.filter(data__month=datetime.now().month)
    entradas = valores.filter(tipo='E')
    saidas = valores.filter(tipo='S')

    total_entradas = calcula_total(entradas, 'valor')
    total_saidas = calcula_total(saidas, 'valor')
    saldo_total = calcula_total(contas, 'valor')

    contas_mes = ContaPagar.objects.all().aggregate(Sum('valor'))

    if contas_mes['valor__sum'] == None:
        contas_mes['valor__sum'] = 0

    despesas_totais = contas_mes['valor__sum'] + total_saidas
    saldo_livre = saldo_total - despesas_totais
    percentual_gastos_essenciais, percentual_gastos_nao_essenciais = calcula_equilibrio_financeiro()

    # contas proximas do vencimento e vencidas
    MES_ATUAL = datetime.now().month
    DIA_ATUAL = datetime.now().day
    
    contas_pagas = ContaPaga.objects.filter(data_pagamento__month=MES_ATUAL).values('conta')

    contas_vencidas = contas_pagar.filter(dia_pagamento__lt=DIA_ATUAL).exclude(id__in=contas_pagas)
    
    contas_proximas_vencimento = contas_pagar.filter(dia_pagamento__lte = DIA_ATUAL + 5).filter(dia_pagamento__gte=DIA_ATUAL).exclude(id__in=contas_pagas)

    return render(request, 'home.html', {'contas': contas, 
                                        'saldo_total': saldo_total,
                                        'total_entradas': total_entradas,
                                        'total_saidas': total_saidas,
                                        'percentual_gastos_essenciais': int(percentual_gastos_essenciais),
                                        'percentual_gastos_nao_essenciais': int(percentual_gastos_nao_essenciais),
                                        'despesas_totais':despesas_totais,
                                        'saldo_livre': saldo_livre,
                                        'contas_vencidas': contas_vencidas,
                                        'contas_proximas_vencimento': contas_proximas_vencimento})

def gerenciar(request):
    contas = Conta.objects.all()
    categorias = Categoria.objects.all()
    #total_contas = contas.aggregate(Sum('valor'))
    
    total_contas = calcula_total(contas, 'valor')

    return render(request, 'gerenciar.html', {'contas': contas, 'total_contas': total_contas, 'categorias': categorias})

def cadastrar_banco(request):
    apelido = request.POST.get('apelido')
    banco = request.POST.get('banco')
    tipo = request.POST.get('tipo')
    valor = request.POST.get('valor')
    icone = request.FILES.get('icone')
    
    if len(apelido.strip()) == 0 or len(valor.strip()) == 0:
        messages.add_message(request, constants.ERROR, 'Preencha todos os campos')
        return redirect('/perfil/gerenciar/')
    
    conta = Conta(
        apelido = apelido,
        banco=banco,
        tipo=tipo,
        valor=valor,
        icone=icone
    )

    conta.save()
    
    messages.add_message(request, constants.SUCCESS, 'Conta cadastrada com sucesso!')
    return redirect('/perfil/gerenciar/')

def deletar_banco(request, id):
    conta = Conta.objects.get(id=id)
    conta.delete()
    
    messages.add_message(request, constants.SUCCESS, 'Conta removida com sucesso')
    return redirect('/perfil/gerenciar/')

def cadastrar_categoria(request):
    nome = request.POST.get('categoria')
    essencial = request.POST.get('essencial')

    if essencial != None and essencial != "essencial":
        messages.add_message(request, constants.ERROR, 'Essencial value error')
        return redirect('/perfil/gerenciar/')
    
    essencial = bool(essencial)
    if len(nome.strip()) == 0 or not(isinstance(essencial, bool)):
        messages.add_message(request, constants.ERROR, 'Preencha todos os campos')
        return redirect('/perfil/gerenciar/')

    categoria = Categoria(
        categoria=nome,
        essencial=essencial
    )

    categoria.save()

    messages.add_message(request, constants.SUCCESS, 'Categoria cadastrada com sucesso')
    return redirect('/perfil/gerenciar/')

def update_categoria(request, id):
    categoria = Categoria.objects.get(id=id)

    categoria.essencial = not categoria.essencial

    categoria.save()

    return redirect('/perfil/gerenciar/')

def dashboard(request):
    dados = {}
    categorias = Categoria.objects.all()
    for categoria in categorias:
        dados[categoria.categoria] = Valores.objects.filter(categoria=categoria).filter(tipo="S").aggregate(Sum('valor'))['valor__sum']
        print(dados[categoria.categoria])
        if dados[categoria.categoria] == None:
            dados[categoria.categoria] = 0
        
    return render(request, 'dashboard.html', {'labels': list(dados.keys()), 'values': list(dados.values())})