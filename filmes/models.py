# filmes/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# =====================================================
# MODEL: FILME
# =====================================================
class Filme(models.Model):
    """Modelo para armazenar informações dos filmes"""
    
    # IDs e identificadores
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True, help_text="ID do filme no TMDB")
    
    # Informações básicas
    titulo = models.CharField(max_length=255)
    titulo_original = models.CharField(max_length=255, blank=True)
    sinopse = models.TextField(blank=True)
    
    # Detalhes técnicos
    ano = models.IntegerField()
    duracao = models.CharField(max_length=50, blank=True)  # Ex: "119 min"
    genero = models.CharField(max_length=100)
    diretor = models.CharField(max_length=255, blank=True)
    elenco = models.TextField(blank=True, help_text="Elenco principal separado por vírgulas")
    
    # Avaliação
    nota = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    
    # Imagens (URLs)
    poster = models.URLField(max_length=500)
    backdrop = models.URLField(max_length=500, blank=True)
    trailer = models.URLField(max_length=500, blank=True, null=True)
    
    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-ano', 'titulo']
        verbose_name = 'Filme'
        verbose_name_plural = 'Filmes'
    
    def __str__(self):
        return f"{self.titulo} ({self.ano})"
    
    def get_nota_estrelas(self):
        """Retorna a nota em formato de estrelas (0-5)"""
        return round(self.nota / 2, 1)


# =====================================================
# MODEL: ESTANTE (Lista de Filmes do Usuário)
# =====================================================
class Estante(models.Model):
    """Modelo para a lista de filmes de cada usuário"""
    
    STATUS_CHOICES = [
        ('assistido', 'Assistido'),
        ('quero_assistir', 'Quero Assistir'),
        ('assistindo', 'Assistindo'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='estante')
    filme = models.ForeignKey(Filme, on_delete=models.CASCADE, related_name='em_estantes')
    
    # Status e avaliação pessoal
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='quero_assistir')
    nota_pessoal = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text="Nota de 0 a 10")
    
    # Datas
    data_adicionado = models.DateTimeField(auto_now_add=True)
    data_assistido = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['usuario', 'filme']
        ordering = ['-data_adicionado']
        verbose_name = 'Item da Estante'
        verbose_name_plural = 'Itens da Estante'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.filme.titulo}"


# =====================================================
# MODEL: COMENTÁRIO
# =====================================================
class Comentario(models.Model):
    """Modelo para comentários dos usuários sobre filmes"""
    
    filme = models.ForeignKey(Filme, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios')
    
    texto = models.TextField()
    spoiler = models.BooleanField(default=False, verbose_name="Contém Spoiler")
    
    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    editado = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
    
    def __str__(self):
        return f"{self.usuario.username} em {self.filme.titulo}"
    
    def total_curtidas(self):
        """Retorna o total de curtidas no comentário"""
        return self.reacoes.filter(tipo='curtida').count()
    
    def usuario_curtiu(self, usuario):
        """Verifica se o usuário curtiu este comentário"""
        return self.reacoes.filter(usuario=usuario, tipo='curtida').exists()


# =====================================================
# MODEL: REAÇÃO (Curtidas nos Comentários)
# =====================================================
class Reacao(models.Model):
    """Modelo para curtidas/reações em comentários"""
    
    TIPO_CHOICES = [
        ('curtida', '❤️ Curtida'),
    ]
    
    comentario = models.ForeignKey(Comentario, on_delete=models.CASCADE, related_name='reacoes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reacoes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='curtida')
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comentario', 'usuario']
        ordering = ['-data_criacao']
        verbose_name = 'Reação'
        verbose_name_plural = 'Reações'
    
    def __str__(self):
        return f"{self.usuario.username} {self.tipo} no comentário de {self.comentario.usuario.username}"
    
    # =====================================================
# MODEL: COMUNIDADE E FÓRUM (Funcionalidade 9)
# =====================================================

class Comunidade(models.Model):
    """O Nicho ou Gênero (Ex: Terror, Sci-Fi, Anos 80)"""
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Identificador na URL (ex: terror)")
    descricao = models.TextField(blank=True)
    imagem_capa = models.URLField(max_length=500, blank=True, help_text="URL da imagem de capa da comunidade")

    class Meta:
        verbose_name = "Comunidade"
        verbose_name_plural = "Comunidades"

    def __str__(self):
        return self.nome

class Topico(models.Model):
    """Uma discussão criada por um usuário dentro de uma comunidade"""
    comunidade = models.ForeignKey(Comunidade, on_delete=models.CASCADE, related_name='topicos')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topicos_criados')
    
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField(help_text="O texto da discussão")
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_criacao'] # Mais recentes primeiro
        verbose_name = "Tópico"
        verbose_name_plural = "Tópicos"

    def __str__(self):
        return self.titulo

class RespostaTopico(models.Model):
    """Respostas dentro de um tópico"""
    topico = models.ForeignKey(Topico, on_delete=models.CASCADE, related_name='respostas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='respostas_topico')
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_criacao'] # Antigos primeiro (ordem de conversa)

    def __str__(self):
        return f"Resposta de {self.usuario.username} em {self.topico}"

        # No final de filmes/models.py

class Notificacao(models.Model):
    remetente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes_enviadas')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes_recebidas')
    filme = models.ForeignKey(Filme, on_delete=models.CASCADE)
    mensagem = models.CharField(max_length=255, blank=True, null=True)
    lida = models.BooleanField(default=False)
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"De {self.remetente} para {self.destinatario}: {self.filme.titulo}"