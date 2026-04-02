from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Insumo, CategoriaInsumo, MovimientoInventario
from .forms import InsumoForm, MovimientoForm


@login_required
def lista_insumos(request):
    insumos = Insumo.objects.filter(activo=True).select_related('categoria')
    alertas = [i for i in insumos if i.necesita_reposicion]
    return render(request, 'inventario/lista.html', {
        'insumos': insumos, 'alertas': alertas
    })


@login_required
def crear_insumo(request):
    if request.method == 'POST':
        form = InsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Insumo registrado.')
            return redirect('inventario:lista')
    else:
        form = InsumoForm()
    return render(request, 'inventario/form.html', {'form': form})


@login_required
def movimiento(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    if request.method == 'POST':
        form = MovimientoForm(request.POST)
        if form.is_valid():
            mov = form.save(commit=False)
            mov.insumo = insumo
            mov.registrado_por = request.user
            if mov.tipo == 'entrada':
                insumo.stock_actual += mov.cantidad
            elif mov.tipo in ('salida', 'vencido'):
                insumo.stock_actual -= mov.cantidad
            elif mov.tipo == 'ajuste':
                insumo.stock_actual = mov.cantidad
            mov.stock_resultante = insumo.stock_actual
            insumo.save()
            mov.save()
            messages.success(request, 'Movimiento registrado.')
    return redirect('inventario:lista')
