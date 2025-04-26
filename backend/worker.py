from .celery_app import celery_app
from .services import tracing, fontbuild
import redis, json

@celery_app.task(name="tasks.build_font")
def build_font(job_id: str, img_bytes: bytes):
    redis_client = redis.Redis(host="redis", port=6379)
    redis_client.hset("jobs", job_id, json.dumps({"state":"TRACING"}))
    svg_map = tracing.extract_glyphs(img_bytes)
    redis_client.hset("jobs", job_id, json.dumps({"state":"BUILDING"}))
    ttf_path = fontbuild.make_font(svg_map, job_id)
    redis_client.hset("jobs", job_id, json.dumps({"state":"DONE", "path": ttf_path}))
