from django import dispatch

content_was_published = dispatch.Signal(providing_args=["site_id", "release_id", "title", "content", "page"])
