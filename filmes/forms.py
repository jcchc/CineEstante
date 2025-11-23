from django import forms
from .models import Topico, RespostaTopico

class TopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ['titulo', 'conteudo']

class RespostaTopicoForm(forms.ModelForm):
    class Meta:
        model = RespostaTopico
        fields = ['texto']