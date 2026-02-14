import logging
from typing import Any

from django.core import mail
from django.core.mail import get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from api.models import EmailSubscriber, Publication
from departmentpublications.settings import DEFAULT_FROM_EMAIL, EMAIL_HOST_USER, SERVER_ADDRESS

logger = logging.getLogger("autoupdate")


def send_update_mail(new_publications: set[Publication]):
    if not EMAIL_HOST_USER:
        logger.debug("Рассылка по электронной почте не настроена. Письма не отправляются")
        return
    tag_map = {}
    con = get_connection()
    con.open()
    subject = 'Новые публикации на вашей кафедре'
    for publ in new_publications:
        tags = []
        for author in publ.authors.all():
            tags.extend(author.tag_set.all())
        for tag in tags:
            tag_map.setdefault(tag, [])
            tag_map[tag].append(publ)
    c = 0
    for subscriber in EmailSubscriber.objects.all():
        context: dict[str, Any] = {"hostname": SERVER_ADDRESS}
        mail_needed = False
        author_filter = lambda x, subscriber=subscriber: any(y.department == subscriber.department for y in x.authors.all())  # noqa: E731
        if not len(subscriber.tags.all()):
            context["by_tag"] = False
            context["publications"] = list(new_publications)
            if subscriber.department:
                context["publications"] = list(filter(author_filter, context["publications"]))
            mail_needed = len(context["publications"]) > 0 or mail_needed
        else:
            context["by_tag"] = True
            context["tags"] = []
            for tag in tag_map:
                if tag in subscriber.tags.all():
                    if subscriber.department:
                        context["tags"].append([tag, list(
                            filter(author_filter, tag_map[tag]))])
                    else:
                        context["tags"].append([tag, tag_map[tag]])
                    mail_needed = len(context["tags"]) > 0 or mail_needed
        if subscriber.department:
            context["department_name"] = subscriber.department.name
        else:
            context["department_name"] = "все кафедры"

        html_message = render_to_string('update_mail_template.html', context)
        plain_message = strip_tags(html_message)
        to = subscriber.email
        if mail_needed:
            mail.send_mail(subject, plain_message, f"Публикации кафедр ВолгГТУ <{DEFAULT_FROM_EMAIL}>", [to],
                           html_message=html_message, connection=con)
            c += 1
    logger.info(f"Отправлено {c} писем подписчикам об обновлении")
    con.close()
