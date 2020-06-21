"""Blogly application."""

from flask import Flask, request, render_template, redirect, flash, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, connect_db, User, Post, Tag, PostTag

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///blogly'
app.config["SECRET_KEY"] = "chickensAreCool"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
debug = DebugToolbarExtension(app)
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False


connect_db(app)
# db.drop_all()
db.create_all()


@app.route("/")
def to_users():
    """Show recent list of posts, most-recent first."""

    return redirect("/users")


@app.route("/users")
def show_users():
    """Show a page with info on all users"""
    users = User.query.all()
    return render_template("list_users.html", users=users)


@app.route("/users/new")
def create_user():
    """Show a form to create a new user"""
    return render_template("create_user.html")


@app.route("/users/new", methods=["POST"])
def adding_user():
    """Handle form submission for creating a new user"""
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    image = request.form["image_url"]
    if len(image) < 20:
        image = "https://merriam-webster.com/assets/mw/images/article/art-wap-landing-mp-lg/egg-3442-4c317615ec1fd800728672f2c168aca5@1x.jpg"
    user = User(first_name=first_name, last_name=last_name, image_url=image)
    db.session.add(user)
    db.session.commit()
    return redirect(f"/users/{user.id}")


@app.route("/users/<int:user_id>")
def show_user(user_id):
    """Show a page with info on a specific user"""
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).all()
    return render_template("user_details.html", user=user, posts=posts)


@app.route("/users/<int:user_id>/edit")
def render_edit_user(user_id):
    """Show a form to edit an existing user"""
    user = User.query.get_or_404(user_id)
    return render_template("edit_user.html", user=user)


@app.route("/users/<int:user_id>/edit", methods=["POST"])
def editing_user(user_id):
    """Handle form submission for updating an existing user"""
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    image = request.form["image_url"]
    user = User.query.get_or_404(user_id)
    if first_name == "":
        first_name = user.first_name
    if last_name == "":
        last_name = user.last_name
    if image == "":
        image = user.image_url
    user.first_name = first_name
    user.last_name = last_name
    user.image_url = image
    db.session.add(user)
    db.session.commit()
    return redirect(f"/users/{user.id}")


@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """Handle form submission for deleting an existing user"""
    user = User.query.get_or_404(user_id)
    # posts = Post.query.filter_by(user_id=user_id).all()
    db.session.delete(user)
    db.session.commit()
    return redirect("/users")


@app.route("/users/<int:user_id>/posts/new")
def show_post_form(user_id):
    """Show a form to create a new post for a specific user"""
    user = User.query.get_or_404(user_id)
    tags = Tag.query.all()
    return render_template("create_post.html", user=user, tags=tags)


@app.route("/users/<int:user_id>/posts/new", methods=["POST"])
def add_post(user_id):
    """Handle form submission for creating a new post for a specific user"""
    title = request.form["title"]
    content = request.form["content"]
    user = User.query.get_or_404(user_id)
    tags = Tag.query.all()
    if title == "" and content != "":
        flash("Please add a title")
        return render_template("create_post.html", user=user, tags=tags)
    if content == "" and title != "":
        flash("Please add some content")
        return render_template("create_post.html", user=user, tags=tags)
    if content == "" and title == "":
        flash("Please add a title and some content")
        return render_template("create_post.html", user=user, tags=tags)
    posts = Post.query.filter_by(user_id=user_id).all()
    for post in posts:
        if title.upper() == post.title.upper():
            flash("This title has already been used, please select a different one")
            return render_template("create_post.html", user=user, tags=tags)
    post = Post(title=title, content=content, user_id=user.id,
                created_at=datetime.now().strftime('%b %d %Y %#I:%M:%S %p'))
    db.session.add(post)

    new_tags = request.form.getlist('tags')

    for tag in new_tags:
        tag_id = Tag.query.filter_by(name=tag).id
        post.posts_tags.append(PostTag(post_id=post.id, tag_id=tag_id))

    db.session.commit()

    return redirect(f"/users/{user_id}")


@app.route("/posts/<int:post_id>")
def show_post(post_id):
    """Show a page with info on a specific post"""
    post = Post.query.filter_by(id=post_id).first()
    user = User.query.filter_by(id=post.user_id).first()
    return render_template("show_post.html", post=post, user=user)


@app.route("/posts/<int:post_id>/edit")
def render_edit_post(post_id):
    """Show a form to edit an existing post"""
    post = Post.query.get_or_404(post_id)
    user = User.query.filter_by(id=post.user_id).first()
    tags = Tag.query.all()
    return render_template("edit_post.html", post=post, user=user, tags=tags)


@app.route("/posts/<int:post_id>/edit", methods=["POST"])
def edit_post(post_id):
    """Handle form submission for updating an existing post"""
    title = request.form["title"]
    content = request.form["content"]
    post = Post.query.get(post_id)
    user = User.query.get(post.user_id)

    if title != "":
        post.title = title
    if content != "":
        post.content = content
    db.session.add(post)

    tags = request.form.getlist('tags')
    post_tags = PostTag.query.filter_by(post_id=post_id).all()

    for post_tag in post_tags:
        if post_tag.tag.name not in tags:
            db.session.delete(post_tag)

    for tag in tags:
        tag_id = Tag.query.filter_by(name=tag).one().id
        current_tag = Tag.query.filter_by(name=tag)
        if current_tag not in post.tags:
            post.posts_tags.append(PostTag(post_id=post.id, tag_id=tag_id))

    db.session.commit()

    # PostTag.query.filter_by(post_id=post_id).delete()
    # db.session.commit()
    # for tag in tags:
    #     tag_id = Tag.query.filter_by(name=tag).first().id
    #     post.posts_tags.append(PostTag(post_id=post.id, tag_id=tag_id))
    #     db.session.commit()

    return redirect(f"/users/{user.id}")


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    """Handle form submission for deleting an existing post"""
    post = Post.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(f"/users/{user.id}")


@app.route("/tags")
def show_tags():
    tags = Tag.query.all()
    return render_template("list_tags.html", tags=tags)


@app.route("/tags/<int:tag_id>")
def show_tag_posts(tag_id):
    tag = Tag.query.get(tag_id)
    return render_template('tag_posts.html', tag=tag)


@app.route("/tags/new")
def show_new_tag_form():
    """Show a form to create a new tag"""
    return render_template("create_new_tag.html")


@app.route("/tags/new", methods=["POST"])
def create_tag():
    """Handle form submission for creating a new tag"""
    title = request.form["tag_name"]
    tags = Tag.query.all()
    for tag in tags:
        if title.upper() == tag.name.upper():
            flash(
                f"The tag \"{title}\" already exists, please create one with a different name")
            return render_template("create_new_tag.html")
    if title == "":
        flash("Please Enter a tag name")
        return render_template("create_new_tag.html")
    new_tag = Tag(name=title)
    db.session.add(new_tag)
    db.session.commit()

    return redirect("/tags")


@app.route("/tags/<int:tag_id>/delete", methods=["POST"])
def delete_tag(tag_id):
    """Handle form submission for deleting an existing tag"""
    tag = Tag.query.get(tag_id)
    db.session.delete(tag)
    db.session.commit()
    return redirect(f"/tags")


@app.route("/tags/<int:tag_id>/edit")
def show_edit_tag_form(tag_id):
    """Show a page with info on a specific tag"""
    tag = Tag.query.get_or_404(tag_id)
    return render_template("edit_tag.html", tag=tag)


@app.route("/tags/<int:tag_id>/edit", methods=["POST"])
def edit_tag(tag_id):
    """Handle form submission for updating an existing tag"""
    name = request.form["tag_name"]
    tags = Tag.query.all()
    current_tag = Tag.query.filter_by(id=tag_id).first()
    if name == "":
        flash("Please Enter a tag name")
        return render_template("edit_tag.html", tag=current_tag)
    for tag in tags:
        if name.upper() == tag.name.upper() and name.upper() != current_tag.name.upper():
            flash(
                f"The tag \"{name}\" already exists, please create one with a different name")
            return render_template("edit_tag.html", tag=current_tag)
        elif name.upper() == current_tag.name.upper():
            flash(
                f"The tag \"{current_tag.name}\" was re-entered, no changes were made to the tag")
            return redirect("/tags")

    edit_tag = Tag.query.get(tag_id)
    edit_tag.name = name
    db.session.add(edit_tag)
    db.session.commit()
    return redirect("/tags")
