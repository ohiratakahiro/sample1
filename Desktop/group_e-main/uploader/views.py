from django.views import generic
from django.urls import reverse_lazy
from .models import Image
from .forms import ImageCreateForm


class ImageListView(generic.ListView):
    model = Image
    template_name = 'uploader/image_list.html'


class ImageCreateView(generic.CreateView):
    model = Image
    form_class = ImageCreateForm
    template_name = 'uploader/image_create.html'
    success_url = reverse_lazy('uploader:image_list')
