# bot_instagram_auto

Bot de automação de comentários para Instagram com sistema de licença por key temporária.

---

## Como funciona

O bot acessa sua conta do Instagram via `sessionid` e automaticamente posta comentários mencionando seguidores em publicações. O acesso ao software é controlado por chaves temporárias geradas pelo desenvolvedor, com tempo de expiração configurável.

---

## Requisitos

- Windows 10 ou superior
- Python 3.10+
- Bibliotecas necessárias:

```
pip install PyQt6 instagrapi pyperclip keyboard
```

---

## Como usar

**1. Clone o repositório**
```
git clone https://github.com/nolonlucas/bot_instagram_auto.git
```

**2. Instale as dependências**
```
pip install PyQt6 instagrapi pyperclip keyboard
```

**3. Execute o bot**
```
python bot_instagram.py
```

**4. Insira sua key de acesso**
Ao abrir, o software solicitará uma chave de acesso temporária. Cole a key fornecida e clique em Entrar.

**5. Insira seu Session ID**
Após autenticado, cole o `sessionid` da sua conta do Instagram no campo indicado e clique em **Iniciar Bot**.

> Para obter o `sessionid`: acesse o Instagram pelo navegador → F12 → Application → Cookies → copie o valor de `sessionid`.

---

## Sistema de Key

As chaves de acesso são geradas pelo arquivo `gerar_key.py` e possuem tempo de expiração definido (30 minutos, 1 hora, etc). Após expirar, o bot é bloqueado automaticamente e uma nova key é necessária para continuar.

---

## Tecnologias

- Python 3
- PyQt6
- instagrapi
- PyInstaller (para compilação em .exe)
