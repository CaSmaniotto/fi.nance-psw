from django.shortcuts import render
from perfil.views import Categoria
from extrato.models import Valores
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Sum
from datetime import datetime

# Create your views here.
def definir_planejamento(request):
    categorias = Categoria.objects.all()
    return render(request, 'definir_planejamento.html', {'categorias': categorias})

@csrf_exempt
def update_valor_categoria(request, id):
    novo_valor = json.load(request)['novo_valor']
    categoria = Categoria.objects.get(id=id)
    categoria.valor_planejamento = novo_valor
    categoria.save()
    #TODO: mensagem de alerta
    return JsonResponse({'status': 'Sucesso'})

def ver_planejamento(request):
    categorias = Categoria.objects.all()

    # Calculo do planejamento no mês
    total = Valores.objects.all().filter(tipo='E').filter(data__month=datetime.now().month).aggregate(Sum('valor'))
    total_gasto = Valores.objects.all().filter(tipo='S').filter(data__month=datetime.now().month).aggregate(Sum('valor'))
    
    total_mes = categorias.aggregate(Sum('valor_planejamento'))
    total_porcentagem_mes = int((total_gasto['valor__sum'] * 100) / total_mes['valor_planejamento__sum'])

    if total['valor__sum'] and total_gasto['valor__sum']:
        total_porcentagem = int((total_gasto['valor__sum'] * 100) / total['valor__sum'])
    total_porcentagem = 0
    total['valor__sum'] = 0

    return render(request, 'ver_planejamento.html', {'categorias': categorias, 'total': total, 'total_gasto': total_gasto, 'total_porcentagem': total_porcentagem, 'total_mes': total_mes, 'total_porcentagem_mes':total_porcentagem_mes})