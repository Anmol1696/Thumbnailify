from .handlers import image, thumbnail

def setup_routes(app):
    app.router.add_post("/images", image, name="image")
    app.router.add_get("/images/{image_id}/thumbnail", thumbnail, name="thumbnail")
