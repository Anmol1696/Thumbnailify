from .handlers import MediaView, MediaViewObject, MediaViewThumbnailObject

def setup_routes(app):
    app.router.add_view("/images", MediaView, name="image")
    app.router.add_view("/images/{id}", MediaViewObject, name="status")
    app.router.add_view("/images/{id}/thumbnail", MediaViewThumbnailObject, name="thumbnail")
