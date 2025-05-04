from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Route


@login_required
def my_routes(request):
    qs = Route.objects.filter(owner=request.user)
    return render(request, 'routes/my_routes.html', {'routes': qs})


@login_required
def create_route(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return render(request, 'routes/create_route.html', {'error': 'Название обязательно'})
        details = []
        for key, desc in request.POST.items():
            if key.startswith('desc_'):
                idx = key.split('_', 1)[1]
                t = request.POST.get(f'type_{idx}')
                v = request.POST.get(f'val_{idx}', '')
                v2 = request.POST.get(f'val2_{idx}', '')
                if t in ['time_range', 'date_range']:
                    details.append({'desc': desc, 'type': t, 'value': [v, v2]})
                else:
                    details.append({'desc': desc, 'type': t, 'value': v})
        Route.objects.create(owner=request.user, name=name, details=details)
        return redirect('routes:my_routes')
    return render(request, 'routes/create_route.html')


@login_required
def view_route(request, route_id):
    route = get_object_or_404(Route, id=route_id, owner=request.user)
    return render(request, 'routes/view_route.html', {'route': route})


@login_required
def edit_route(request, route_id):
    route = get_object_or_404(Route, id=route_id, owner=request.user)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        total = int(request.POST.get('total_fields', 0))
        details = []
        for i in range(total):
            desc = request.POST.get(f'desc_{i}')
            t = request.POST.get(f'type_{i}')
            v1 = request.POST.get(f'val_{i}', '')
            v2 = request.POST.get(f'val2_{i}', '')
            if t in ['time_range', 'date_range']:
                details.append({'desc': desc, 'type': t, 'value': [v1, v2]})
            else:
                details.append({'desc': desc, 'type': t, 'value': v1})
        if name:
            route.name = name
            route.details = details
            route.save()
        return redirect('routes:view_route', route_id=route.id)
    return render(request, 'routes/edit_route.html', {'route': route})


def home_redirect(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect('accounts:welcome')
    return redirect('accounts:login')
