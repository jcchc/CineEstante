# filmes/views.py
from django.contrib.auth.models import User
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Filme, Estante, Comentario, Reacao, Comunidade, Topico, RespostaTopico, Notificacao
from .forms import TopicoForm, RespostaTopicoForm


# =====================================================
# VIEWS ANTIGAS (Mantidas)
# =====================================================

@login_required
def editar_perfil(request):
    return render(request, 'perfil/editar.html')

@login_required
def lista_filmes(request):
    """Lista de filmes da estante do usuário"""
    filmes_estante = Estante.objects.filter(usuario=request.user).select_related('filme')
    
    context = {
        'filmes_estante': filmes_estante,
    }
    return render(request, 'filmes/lista.html', context)

@login_required
def buscar_filmes(request):
    return render(request, 'filmes/buscar.html')


# =====================================================
# HOME VIEW 100% DINÂMICA (Conectada ao Banco)
# =====================================================

def home_view(request):
    """View Dinâmica que puxa do Banco de Dados"""
    
    # 1. Tenta pegar os filmes 'famosos' que você gosta para o banner
    titulos_destaque = ['Tron: Ares', 'Coração de Lutador', 'Paddington no Peru', 'Nosferatu']
    filmes_destaque = Filme.objects.filter(titulo__in=titulos_destaque)
    
    # Se não achar (banco novo), pega os 4 últimos adicionados
    if not filmes_destaque.exists():
        filmes_destaque = Filme.objects.all().order_by('-id')[:4]

    # 2. Monta os dados para o Carrossel
    dados_cartaz = []
    for filme in filmes_destaque:
        dados_cartaz.append({
            'id': filme.id,
            'titulo': filme.titulo,
            'sinopse': filme.sinopse[:150] + '...' if filme.sinopse else '',
            'backdrop': filme.backdrop if filme.backdrop else filme.poster,
            'poster': filme.poster,
            'ano': filme.ano,
            'duracao': filme.duracao,
            'genero': filme.genero,
            'nota': float(filme.nota) if filme.nota else 0,
            'trailer_url': filme.trailer if filme.trailer else '',
        })
    
    # 3. Outras Listas
    top10 = Filme.objects.order_by('-nota')[:10]
    em_alta = Filme.objects.order_by('?')[:6]
    indicacoes = Filme.objects.order_by('?')[:6]

    # 4. Estante do Usuário
    filmes_na_estante = []
    if request.user.is_authenticated:
        filmes_na_estante = list(Estante.objects.filter(usuario=request.user).values_list('filme_id', flat=True))

    context = {
        'filmes_cartaz': json.dumps(dados_cartaz),
        'top10_semanal': top10,
        'indicacoes': indicacoes,
        'em_alta': em_alta,
        'filmes_na_estante': filmes_na_estante,
    }
    return render(request, 'home.html', context)


# =====================================================
# NOVAS VIEWS - Sistema de Filmes e Comentários
# =====================================================

@login_required
def filme_detalhes(request, filme_id):
    """Página de detalhes do filme com comentários"""
    
    # Busca o filme no banco
    filme = get_object_or_404(Filme, id=filme_id)
    
    # Verifica se usuário já tem na estante
    na_estante = Estante.objects.filter(usuario=request.user, filme=filme).exists()
    
    # Busca comentários do filme
    comentarios = filme.comentarios.select_related('usuario').all()
    
    # Para cada comentário, verifica se usuário curtiu
    for comentario in comentarios:
        comentario.usuario_curtiu_comentario = comentario.usuario_curtiu(request.user)
    
    context = {
        'filme': filme,
        'na_estante': na_estante,
        'comentarios': comentarios,
        'total_comentarios': comentarios.count(),
    }
    
    return render(request, 'filmes/detalhes.html', context)


@login_required
@require_POST
def adicionar_filme_estante(request, filme_id):
    """Adiciona filme à estante do usuário"""
    
    filme = get_object_or_404(Filme, id=filme_id)
    
    # Cria ou busca o item na estante
    estante, criado = Estante.objects.get_or_create(
        usuario=request.user,
        filme=filme,
        defaults={'status': 'quero_assistir'}
    )
    
    if criado:
        messages.success(request, f'"{filme.titulo}" foi adicionado à sua estante!')
    else:
        messages.info(request, f'"{filme.titulo}" já está na sua estante!')
    
    # Retorna JSON se for requisição AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'criado': criado,
            'message': f'"{filme.titulo}" foi adicionado à sua estante!' if criado else f'"{filme.titulo}" já está na sua estante!'
        })
    
    # Se não for AJAX, redireciona de volta
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def remover_filme_estante(request, filme_id):
    """Remove filme da estante do usuário"""
    
    filme = get_object_or_404(Filme, id=filme_id)
    
    try:
        estante = Estante.objects.get(usuario=request.user, filme=filme)
        estante.delete()
        messages.success(request, f'"{filme.titulo}" foi removido da sua estante!')
        sucesso = True
    except Estante.DoesNotExist:
        messages.warning(request, f'"{filme.titulo}" não está na sua estante!')
        sucesso = False
    
    # Retorna JSON se for requisição AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': sucesso})
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def adicionar_comentario(request, filme_id):
    """Adiciona comentário ao filme (COM SUPORTE A SPOILER)"""
    
    filme = get_object_or_404(Filme, id=filme_id)
    texto = request.POST.get('texto', '').strip()
    # Verifica se o checkbox 'spoiler' foi marcado no HTML
    tem_spoiler = request.POST.get('spoiler') == 'on'
    
    if not texto:
        messages.error(request, 'O comentário não pode estar vazio!')
        return redirect('filmes:filme_detalhes', filme_id=filme_id)
    
    # Cria o comentário salvando o status do spoiler
    comentario = Comentario.objects.create(
        filme=filme,
        usuario=request.user,
        texto=texto,
        spoiler=tem_spoiler
    )
    
    messages.success(request, 'Comentário adicionado com sucesso!')
    
    # Retorna JSON se for requisição AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'comentario': {
                'id': comentario.id,
                'texto': comentario.texto,
                'usuario': comentario.usuario.username,
                'foto_perfil': comentario.usuario.perfil.get_foto_url() if hasattr(comentario.usuario, 'perfil') else '',
                'data': comentario.data_criacao.strftime('%d/%m/%Y %H:%M'),
                'spoiler': tem_spoiler
            }
        })
    
    return redirect('filmes:filme_detalhes', filme_id=filme_id)


@login_required
@require_POST
def curtir_comentario(request, comentario_id):
    """Curtir ou descurtir um comentário"""
    
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verifica se já curtiu
    reacao = Reacao.objects.filter(comentario=comentario, usuario=request.user).first()
    
    if reacao:
        # Se já curtiu, remove a curtida
        reacao.delete()
        curtiu = False
        mensagem = 'Curtida removida!'
    else:
        # Se não curtiu, adiciona curtida
        Reacao.objects.create(
            comentario=comentario,
            usuario=request.user,
            tipo='curtida'
        )
        curtiu = True
        mensagem = 'Comentário curtido!'
    
    total_curtidas = comentario.total_curtidas()
    
    # Retorna JSON para AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'curtiu': curtiu,
            'total_curtidas': total_curtidas,
            'message': mensagem
        })
    
    messages.success(request, mensagem)
    return redirect('filmes:filme_detalhes', filme_id=comentario.filme.id)


@login_required
@require_POST
def deletar_comentario(request, comentario_id):
    """Deleta comentário (apenas o próprio usuário pode deletar)"""
    
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verifica se o usuário é o dono do comentário
    if comentario.usuario != request.user:
        messages.error(request, 'Você não pode deletar este comentário!')
        return redirect('filmes:filme_detalhes', filme_id=comentario.filme.id)
    
    filme_id = comentario.filme.id
    comentario.delete()
    
    messages.success(request, 'Comentário deletado com sucesso!')
    
    # Retorna JSON se for requisição AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('filmes:filme_detalhes', filme_id=filme_id)


# =====================================================
# COMUNIDADES E FÓRUM
# =====================================================

def lista_comunidades(request):
    comunidades = Comunidade.objects.all()
    return render(request, 'filmes/comunidades.html', {'comunidades': comunidades})

def detalhe_comunidade(request, slug):
    comunidade = get_object_or_404(Comunidade, slug=slug)
    topicos = comunidade.topicos.all().order_by('-data_criacao')
    return render(request, 'filmes/comunidade_detalhe.html', {'comunidade': comunidade, 'topicos': topicos})

@login_required
def criar_topico(request, slug):
    comunidade = get_object_or_404(Comunidade, slug=slug)
    if request.method == 'POST':
        form = TopicoForm(request.POST)
        if form.is_valid():
            topico = form.save(commit=False)
            topico.comunidade = comunidade
            topico.usuario = request.user
            topico.save()
            return redirect('filmes:detalhe_comunidade', slug=slug)
    else:
        form = TopicoForm()
    return render(request, 'filmes/criar_topico.html', {'comunidade': comunidade, 'form': form})

def detalhe_topico(request, topico_id):
    topico = get_object_or_404(Topico, id=topico_id)
    respostas = topico.respostas.all()
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = RespostaTopicoForm(request.POST)
        if form.is_valid():
            resposta = form.save(commit=False)
            resposta.topico = topico
            resposta.usuario = request.user
            resposta.save()
            return redirect('filmes:detalhe_topico', topico_id=topico.id)
    else:
        form = RespostaTopicoForm()
        
    return render(request, 'filmes/topico_detalhe.html', {'topico': topico, 'respostas': respostas, 'form': form})


# =====================================================
# NOTIFICAÇÕES E SUGESTÕES (NOVO)
# =====================================================

@login_required
def enviar_sugestao(request, filme_id):
    filme = get_object_or_404(Filme, id=filme_id)
    
    if request.method == 'POST':
        username_dest = request.POST.get('username')
        mensagem = request.POST.get('mensagem')
        
        try:
            destinatario = User.objects.get(username=username_dest)
            if destinatario == request.user:
                messages.warning(request, 'Você não pode recomendar filmes para si mesmo!')
            else:
                Notificacao.objects.create(
                    remetente=request.user,
                    destinatario=destinatario,
                    filme=filme,
                    mensagem=mensagem
                )
                messages.success(request, f'Recomendação enviada para {destinatario.username}!')
        except User.DoesNotExist:
            messages.error(request, f'Usuário "{username_dest}" não encontrado.')
            
    return redirect('filmes:filme_detalhes', filme_id=filme.id)

@login_required
def ver_notificacoes(request):
    notificacoes = Notificacao.objects.filter(destinatario=request.user).order_by('-data_envio')
    nao_lidas = notificacoes.filter(lida=False).count()
    return render(request, 'filmes/notificacoes.html', {'notificacoes': notificacoes, 'nao_lidas': nao_lidas})

@login_required
def marcar_como_lida(request, notificacao_id):
    notificacao = get_object_or_404(Notificacao, id=notificacao_id)
    if notificacao.destinatario == request.user:
        notificacao.lida = True
        notificacao.save()
    return redirect('filmes:ver_notificacoes')