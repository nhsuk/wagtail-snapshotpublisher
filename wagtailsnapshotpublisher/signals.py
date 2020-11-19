from django import dispatch

content_was_published = dispatch.Signal(providing_args=["site_id", "release_id", "title", "content", "page"])
content_was_unpublsished = dispatch.Signal(providing_args=["site_id", "release_id", "title", "content", "page"])
release_was_staged = dispatch.Signal(providing_args=["release"])
reindex_release = dispatch.Signal(providing_args=["release"])