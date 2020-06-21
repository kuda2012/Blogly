from unittest import TestCase

from app import app
from models import db, User, Post

# Use test database and don't clutter tests with SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///users_test'
app.config['SQLALCHEMY_ECHO'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

db.drop_all()
db.create_all()


class UserViewsTestCase(TestCase):
    """Tests for views for Users"""

    def setUp(self):
        """Add sample user and post."""
        Post.query.delete()
        User.query.delete()
        user = User(first_name="TestFirstName", last_name="TestLastName", image_url="https://tinyurl.com/y77znsdx")
        db.session.add(user)
        db.session.commit()
        post = Post(title="TestTitle", content="TestContent", user_id = user.id)
        db.session.add(post)
        db.session.commit()
        self.user = user
        self.user_id = user.id
        self.post = post
        self.post_id = post.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_list_users(self):
        with app.test_client() as client:
            """Test that users are listed"""
            resp = client.get("/users")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>Users</h1>", html)
            self.assertIn('TestFirstName', html)

    def test_create_user(self):
        with app.test_client() as client:
            """Test that user is created and shown"""
            resp = client.get("/users/new")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>Create User</h1>", html)
            self.assertIn("First Name", html)
    def test_user_details(self):
        with app.test_client() as client:
            """Test if details of given user are shown"""
            resp = client.get(f"/users/{self.user_id}")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('TestFirstName TestLastName', html)
            self.assertIn("View All Users", html)
            self.assertIn('<h1>Posts</h1>', html)     
    def test_edit_user(self):
        with app.test_client() as client:
            """Test if user names and images are changed"""
            d = {"first_name":"Kuda", "last_name":"", "image_url":""}
            resp = client.post(f"/users/{self.user_id}/edit", data = d, follow_redirects = True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("TestFirstName", html)
    
    def test_delete_user(self):
        with app.test_client() as client:
            """Test if user is deleted"""
            resp = client.post(f"/users/{self.user_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("TestFirstName", html)

    def test_show_create_post_form(self):
        with app.test_client() as client:
             """Test if form is shown to create post"""
             resp = client.get(f"/users/{self.user_id}/posts/new")
             html = resp.get_data(as_text=True)
             self.assertEqual(resp.status_code, 200)
             self.assertIn("TestFirstName TestLastName", html)                 
             self.assertIn("Title", html)             
             self.assertIn("Content", html)
    def test_create_post(self):
        with app.test_client() as client:
             """Test if post is created"""
             d = {"title":"The Title", "content":"The Content"}
             resp = client.post(f"/users/{self.user_id}/posts/new",data = d, follow_redirects = True)
             html = resp.get_data(as_text=True)
             self.assertEqual(resp.status_code, 200)             
             self.assertIn("<li>The Title</li>", html)

    def test_post_no_title_no_content(self):
        with app.test_client() as client:
             """Test if flash msg if not title or content enterd for post creation"""
             d = {"title":"", "content":""}
             resp = client.post(f"/users/{self.user_id}/posts/new",data = d, follow_redirects = True)
             html = resp.get_data(as_text=True)
             self.assertEqual(resp.status_code, 200)             
             self.assertIn("Please add a title and some content", html)


    def test_post_details(self):
        with app.test_client() as client:
             """Test show post details"""
             resp = client.get(f"/posts/{self.post_id}")
             html = resp.get_data(as_text=True)
             self.assertEqual(resp.status_code, 200)
             self.assertIn(f"<h1>{self.post.title}</h1>", html)
             self.assertIn(f"<b><i>{self.user.first_name} {self.user.last_name}</i></b>", html)                