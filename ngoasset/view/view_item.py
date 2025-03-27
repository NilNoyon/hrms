from fixedasset.views import *


def item_list(request):

    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['name'] = request.POST.get('name').lower()
        request.POST['specification'] = request.POST.get('specification').lower()

        status = 0
        item_obj = FAItems.objects
        # checking if the same name and the specification already exists
        if item_obj.filter(name=request.POST['name'], specification=request.POST['specification']).exists():
            status = 1

        if status == 1:
            messages.warning(request, "This Item Already Exists!")
            return redirect('fa:item_list')

        sub_classification = request.POST.get('subclassification', '')
        try:
            sub_classification_id = int(sub_classification)
            try:
                sub_classification = FASubClassification.objects.get(id=sub_classification_id)
            except FASubClassification.DoesNotExist:
                data = {'name': sub_classification}
                status = checkDuplicate(request, FASubClassification)
                if status == 0:
                    return redirect('fa:item_list')
                form = FASubClassificationForm(data)
                if form.is_valid():
                    sub_classification = form.save()

        except ValueError:
            data = {'name': sub_classification}
            status = checkDuplicate(request, FASubClassification)
            if status == 0:
                return redirect('fa:item_list')
            form = FASubClassificationForm(data)
            if form.is_valid():
                sub_classification = form.save()

        request.POST['subclassification'] = sub_classification.id
        form = FAItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Stored!")
            return redirect('fa:item_list')
        else:
            for field in form:
                for error in field.errors:
                    messages.warning(request, "%s : %s" % (field.name, error))

    template_name = "item/list.html"
    uom_list = INVUoM.objects.order_by('-id').all().values('id', 'short_name')

    action_name = "Add Item"
    action_url = reverse('fa:item_list')

    context = {'uom_list': uom_list, 'action_name': action_name, 'action_url': action_url, 'countries': countries}
    return render(request, template_name, context)

@csrf_exempt
def get_fa_item_for_datatable(request):
    data_list = []
    search_text = request.POST.get('search[value]', '')
    start = int(request.POST.get('start', 0))

    item_list = FAItems.objects.order_by('-id').all()

    if search_text:
        item_list = item_list.filter(
            Q(name__icontains=search_text)|
            Q(specification__icontains=search_text)|
            Q(brand__icontains=search_text)|
            Q(uom__name__icontains=search_text)|
            Q(origin__icontains=search_text) |
            Q(subclassification__name__icontains=search_text)
        )

    item_list = item_list.order_by("-id")[start:start + 20]
    for item in item_list:
        name = item.name
        category = item.specification
        brand = item.brand
        uom = item.uom.short_name if item.uom else "N/A"
        origin = item.origin.name if item.origin else 'N/A'
        subclassification = item.subclassification.name if item.subclassification else "N/A"
        edit_url = reverse("fa:item_update", kwargs={'id': item.id})
        action = '<a class="h4 m-r-10 text-success" href="'+edit_url+'" class="h4 text-danger">'+'<span class="icon">'+'<i class="ti-pencil-alt"></i>'+'</span></a>'

        data = [name, category, brand, uom, origin, subclassification, action]
        data_list.append(data)
    return JsonResponse(data_list, safe=False)


@login
def item_update(request, id):
    item = get_object_or_404(FAItems, id=id)

    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['name'] = request.POST.get('name').lower()
        request.POST['specification'] = request.POST.get('specification').lower()

        status = 0
        item_obj = FAItems.objects
        # checking if the same name and the specification already exists
        if item_obj.filter(name=request.POST['name'], specification=request.POST['specification']).exists():
            status = 1

        if status == 1:
            messages.warning(request, "This Item Already Exists!")
            return redirect('fa:item_list')

        sub_classification = request.POST.get('subclassification', '')
        try:
            sub_classification_id = int(sub_classification)
            try:
                sub_classification = FASubClassification.objects.get(id=sub_classification_id)
            except FASubClassification.DoesNotExist:
                data = {'name': sub_classification}
                status = checkDuplicate(request, FASubClassification)
                if status == 0:
                    return redirect('fa:item_list')
                form = FASubClassificationForm(data)
                if form.is_valid():
                    sub_classification = form.save()

        except ValueError:
            data = {'name': sub_classification}
            status = checkDuplicate(request, FASubClassification)
            if status == 0:
                return redirect('fa:item_list')
            form = FASubClassificationForm(data)
            if form.is_valid():
                sub_classification = form.save()

        request.POST = request.POST.copy()
        request.POST['subclassification'] = sub_classification.id
        form = FAItemForm(request.POST, instance=item)
        if status == 1:
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully Updated!")
                return redirect(request.META.get('HTTP_REFERER'))
            else:
                for field in form:
                    for error in field.errors:
                        messages.warning(request, "%s : %s" % (field.name, error))

    template_name = "item/list.html"
    uom_list = INVUoM.objects.order_by('-id').all().values('id', 'short_name')
    action_name = "Update Item"
    action_url = reverse_lazy('fa:item_update', kwargs={'id': item.id})

    context = {'item': item, 'uom_list': uom_list,'countries': countries,
               'action_name': action_name, 'action_url': action_url}
    return render(request, template_name, context)


def get_fa_subclassification(request):
    item_name = request.GET.get('q[term]', '')
    item_list = FASubClassification.objects.filter(name__icontains=item_name).order_by('name').values('id', 'name')
    new_list = []

    for item in item_list:
        new_list.append({'id': item['id'], 'text': item['name']})
    return JsonResponse({'items': new_list}, safe=False)


def get_fa_items(request):
    item_name = request.GET.get('q[term]', '')
    item_list = FAItems.objects.filter(name__icontains=item_name).order_by('name').values('id', 'name')
    new_list = []

    for item in item_list:
        new_list.append({'id': item['id'], 'text': item['name']})

    return JsonResponse({'items': new_list}, safe=False)

@csrf_exempt
def get_fa_item_details(request):
    item_id = request.POST.get('item')
    get_item = FAItems.objects.get(id=item_id)
    data = {
        'id': get_item.id,
        'name': get_item.name,
        'specification': get_item.specification,
        'brand': get_item.brand,
        'origin': get_item.origin.code,
        'subclassification': get_item.subclassification.id,
        'subclassification_name': get_item.subclassification.name
    }
    return JsonResponse(data, safe=False)