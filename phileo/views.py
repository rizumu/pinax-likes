from django.http import HttpResponse, HttpResponseForbidden
from django.utils import simplejson as json
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from phileo.models import Like
from phileo.signals import object_liked, object_unliked


@login_required
@require_POST
def like_toggle(request, content_type_id, object_id):
    content_type = get_object_or_404(ContentType, pk=content_type_id)
    obj = content_type.get_object_for_this_type(pk=object_id)
    
    if not request.user.has_perm("phileo.can_like", obj):
        return HttpResponseForbidden()
    
    like, created = Like.objects.get_or_create(
        sender=request.user,
        receiver_content_type=content_type,
        receiver_object_id=object_id
    )
    
    if created:
        object_liked.send(sender=Like, like=like, request=request)
    else:
        like.delete()
        object_unliked.send(
            sender=Like,
            object=obj,
            request=request
        )
    
    if request.is_ajax():
        return HttpResponse(json.dumps({
            "likes_count": Like.objects.filter(
                receiver_content_type=content_type,
                receiver_object_id=object_id
            ).count(),
            "liked": created,
        
        }), mimetype="application/json")
    
    return redirect(request.META["HTTP_REFERER"])
