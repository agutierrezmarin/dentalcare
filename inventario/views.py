from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import Insumo, CategoriaInsumo, MovimientoInventario
from .forms import InsumoForm, MovimientoForm, CategoriaInsumoForm
from dentalcare.decorators import solo_admin, admin_o_recepcion


# ── Inventario principal ───────────────────────────────────────────────

@login_required
@admin_o_recepcion
def lista_insumos(request):
    hoy = timezone.now().date()
    limite = hoy + timedelta(days=30)

    insumos = Insumo.objects.filter(activo=True).select_related('categoria')

    stock_bajo    = [i for i in insumos if i.necesita_reposicion]
    vencidos      = [i for i in insumos if i.esta_vencido]
    por_vencer    = [i for i in insumos if i.proxima_expiracion]

    return render(request, 'inventario/lista.html', {
        'insumos':    insumos,
        'alertas':    stock_bajo,
        'vencidos':   vencidos,
        'por_vencer': por_vencer,
    })


@login_required
@admin_o_recepcion
def crear_insumo(request):
    if request.method == 'POST':
        form = InsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Insumo registrado exitosamente.')
            return redirect('inventario:lista')
    else:
        form = InsumoForm()
    return render(request, 'inventario/form.html', {'form': form, 'titulo': 'Nuevo insumo'})


@login_required
@admin_o_recepcion
def editar_insumo(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    if request.method == 'POST':
        form = InsumoForm(request.POST, instance=insumo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Insumo "{insumo.nombre}" actualizado.')
            return redirect('inventario:lista')
    else:
        form = InsumoForm(instance=insumo)
    return render(request, 'inventario/form.html', {
        'form': form,
        'titulo': f'Editar: {insumo.nombre}',
        'insumo': insumo,
    })


@login_required
@admin_o_recepcion
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


# ── Categorías (solo admin) ────────────────────────────────────────────

@login_required
@solo_admin
def categorias_lista(request):
    categorias = CategoriaInsumo.objects.all()
    form = CategoriaInsumoForm()
    return render(request, 'inventario/categorias.html', {
        'categorias': categorias,
        'form': form,
    })


@login_required
@solo_admin
def categoria_crear(request):
    if request.method == 'POST':
        form = CategoriaInsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada.')
        else:
            messages.warning(request, 'Nombre de categoría inválido.')
    return redirect('inventario:categorias')


@login_required
@solo_admin
def categoria_editar(request, pk):
    cat = get_object_or_404(CategoriaInsumo, pk=pk)
    if request.method == 'POST':
        form = CategoriaInsumoForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada.')
        else:
            messages.warning(request, 'Datos inválidos.')
    return redirect('inventario:categorias')


@login_required
@solo_admin
def categoria_eliminar(request, pk):
    cat = get_object_or_404(CategoriaInsumo, pk=pk)
    if request.method == 'POST':
        nombre = cat.nombre
        cat.delete()
        messages.success(request, f'Categoría "{nombre}" eliminada.')
    return redirect('inventario:categorias')
