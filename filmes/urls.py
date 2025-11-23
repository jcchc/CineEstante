from django.urls import path
from . import views

app_name = 'filmes'

urlpatterns = [
    # --- Home e Listas ---
    path('', views.home_view, name='home'), # A Home agora é a raiz do app filmes se estiver incluso na raiz do projeto
    path('lista/', views.lista_filmes, name='lista'),
    path('buscar/', views.buscar_filmes, name='buscar'),

    # --- Detalhes do Filme e Ações ---
    path('filme/<int:filme_id>/', views.filme_detalhes, name='filme_detalhes'),
    path('filme/<int:filme_id>/estante/adicionar/', views.adicionar_filme_estante, name='adicionar_filme_estante'),
    path('filme/<int:filme_id>/estante/remover/', views.remover_filme_estante, name='remover_filme_estante'),
    
    # --- Comentários ---
    path('filme/<int:filme_id>/comentario/adicionar/', views.adicionar_comentario, name='adicionar_comentario'),
    path('comentario/<int:comentario_id>/curtir/', views.curtir_comentario, name='curtir_comentario'),
    path('comentario/<int:comentario_id>/deletar/', views.deletar_comentario, name='deletar_comentario'),

    # --- Comunidades (Fórum) ---
    path('comunidades/', views.lista_comunidades, name='lista_comunidades'),
    path('comunidade/<slug:slug>/', views.detalhe_comunidade, name='detalhe_comunidade'),
    path('comunidade/<slug:slug>/novo/', views.criar_topico, name='criar_topico'),
    path('topico/<int:topico_id>/', views.detalhe_topico, name='detalhe_topico'),

    # --- NOTIFICAÇÕES E SUGESTÕES (O QUE FALTAVA) ---
    path('filme/<int:filme_id>/sugerir/', views.enviar_sugestao, name='enviar_sugestao'),
    path('notificacoes/', views.ver_notificacoes, name='ver_notificacoes'),
    path('notificacoes/<int:notificacao_id>/lida/', views.marcar_como_lida, name='marcar_como_lida'),
]