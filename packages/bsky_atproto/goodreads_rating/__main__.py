import os
import httpx
from bs4 import BeautifulSoup
from atproto import Client, models

def get_metadata(url):
    # Get website and parse the content
    response = httpx.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the title
    title = ""
    og_title_tag = soup.find("meta", property="og:title")
    if og_title_tag:
        title = og_title_tag["content"]
    else:
        if soup.title:
            title = soup.title.string

    # Extract the description
    description = ""
    og_description_tag = soup.find("meta", property="og:description")
    if og_description_tag:
        description = og_description_tag["content"]
    else:
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            description = meta_description['content']

    # Extract the og:image url
    og_image = None
    image_tag = soup.find("meta", property="og:image")
    if image_tag:
        og_image = image_tag["content"]

    return title, description, og_image

def main(args):
    user_rating = args.get('user_rating')
    book_title = args.get('book_title')
    author_name = args.get('author_name')
    book_url = args.get('book_url')

    # Connect to bsky
    client = Client()
    client.login(os.getenv('BSKY_USER'), os.getenv('BSKY_PASSWORD'))

    # Extract metadata
    title, description, img_url = get_metadata(book_url)

    # Deal with thumbnail preview
    thumb_blob = None
    if img_url:
        # Download image and upload to bsky it as a blob
        img_data = httpx.get(img_url).content
        thumb_blob = client.upload_blob(img_data).blob

    # Create the embedded link object
    embed_external = models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(title=title, description=description, uri=book_url, thumb=thumb_blob)
    )

    # Post!
    post_text = f"{user_rating} of 5 stars to {book_title} by {author_name}"
    client.send_post(text=post_text, embed=embed_external)

    return {"body": post_text}
