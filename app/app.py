from flask import Flask, render_template, redirect, request, url_for, flash
from flask_mail import Mail, Message
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
application = app

app.config['MAIL_SERVER'] = 'mail.pandagh.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'rawadie@pandagh.com'
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Replace with your actual email password
app.config['MAIL_DEFAULT_SENDER'] = 'orders@pandagh.com'

mail = Mail(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Allowed file extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('quote_now.html')

@app.route('/quote', methods=['POST'])
def request_quote():
    try:
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        company = request.form.get('company', 'N/A')
        items = request.form['items']
        details = request.form['details']

        # Handling file uploads
        uploaded_files = request.files.getlist('sample_images')
        image_filenames = []

        # Save uploaded images and store filenames
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_filenames.append(filepath)

        # Compose the email to the owner (HTML with embedded images)
        owner_msg = Message('New Quote Request from Panda Shop',
                            sender='orders@pandagh.com',
                            recipients=['info@pandagh.com'])
        
        # Constructing HTML email for the owner
        owner_msg.html = f"""
        <h3>New Quote Request from Panda Shop</h3>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Contact:</strong> {contact}</p>
        <p><strong>Company:</strong> {company}</p>
        <p><strong>Items:</strong> {items}</p>
        <p><strong>Details:</strong> {details}</p>
        <p>Attached below are the sample images uploaded by the customer:</p>
        """

        # Attach images to the email sent to the owner (with Content-ID for embedding)
        for i, image in enumerate(image_filenames):
            with app.open_resource(image) as img:
                owner_msg.attach(
                    filename=os.path.basename(image),
                    content_type="image/*",
                    data=img.read(),
                    disposition='inline',  # Attach as inline content
                    headers={'Content-ID': f'<image{i}>'}  # Set the Content-ID
                )
                owner_msg.html += f'<p><img src="cid:image{i}" alt="Sample Image {i+1}"></p>'


        mail.send(owner_msg)

        # Compose the email to the customer (HTML email)
        customer_msg = Message('Your Quote Request has been received!',
                               sender='orders@pandagh.com',
                               recipients=[email])
        
        # Constructing HTML email for the customer
        customer_msg.html = f"""
        <h3>Hi {name},</h3>
        <p>Thank you for your interest in purchasing wholesale from Panda Shop.</p>
        <p>We have received your request for a quote with the following details:</p>
        <p><strong>Contact:</strong> {contact}</p>
        <p><strong>Company:</strong> {company}</p>
        <p><strong>Items:</strong> {items}</p>
        <p><strong>Details:</strong> {details}</p>
        <p>Our team will reach out to you shortly to discuss your request and provide a quote.</p>
        <p>Best regards,<br>Panda Shop Team</p>
        """

        mail.send(customer_msg)

        # Flash a success message
        flash('Your quote request has been submitted successfully! We will get back to you soon.', 'success')

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
