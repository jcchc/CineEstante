from django.contrib import admin
from .models import Filme, Estante, Comentario, Reacao, Comunidade, Topico, RespostaTopico

# Configuração para FILMES
@admin.register(Filme)
class FilmeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ano', 'genero', 'nota')
    search_fields = ('titulo',)
    list_filter = ('genero', 'ano')

# Configuração para COMUNIDADES
@admin.register(Comunidade)
class ComunidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)} # Preenche o slug automaticamente

# Registrando os outros modelos simples
admin.site.register(Estante)
admin.site.register(Comentario)
admin.site.register(Reacao)
admin.site.register(Topico)
admin.site.register(RespostaTopico)