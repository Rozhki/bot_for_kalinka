import html


def esc(text) -> str:
    return html.escape(str(text))


def user_link(telegram_id: int, username: str | None, full_name: str) -> str:
    # Ссылка на профиль автора заявки
    if username:
        return f'@{esc(username)}'
    return f'<a href="tg://user?id={telegram_id}">{esc(full_name)}</a> (id {telegram_id})'
