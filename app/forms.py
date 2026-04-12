from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField,EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import re
def strong_password(form, field):
    password = field.data

    if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', password):
        raise ValidationError(
            "Password must be 8+ characters and include letters, numbers, and symbols"
        )

class RegisterForm(FlaskForm):

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=50)]
    )

    email = EmailField(validators=[DataRequired(), Email(message="Enter a valid email")])

    phone = StringField(
        "Phone Number",
        validators=[DataRequired(), Length(min=10, max=15)]
    )

    account_number = StringField(
        "Account Number",
        validators=[DataRequired(), Length(min=8, max=20)]
    )

    bank_name = StringField(
        "Bank Name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    branch = StringField(
        "Branch",
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    ifsc_code = StringField(
        "IFSC Code",
        validators=[DataRequired(), Length(min=6, max=20)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), strong_password]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match")
        ]
    )

    role = SelectField(
        "Role",
        choices=[("user", "User")],
        default="user"
    )

    submit = SubmitField("Register")