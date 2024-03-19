from django.shortcuts import render,HttpResponse,redirect

from .forms import RegistrationForm
from accounts.models import Account
from django.contrib import messages,auth
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from carts.models import Cart
from carts.views import _cart_id,CartItem
from django.contrib.auth.decorators import login_required
# Create your views here.
def register(request):
    form = RegistrationForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            user = Account.objects.create_user(first_name=first_name,last_name=last_name,email=email,username=username,password=password)
            user.phone_number = phone_number
            user.save()
            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            messages.success(request,"Account Created for "+ username+"! Verify your email to use your account")
            return redirect('login/?command=verification&email='+to_email)
    else :
        form = RegistrationForm()
    context = {
        'form':form,
    }
    return render(request,'accounts/register.html',context=context)
def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email,password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    for item in cart_item:
                        item.user = user
                        user.save()
            except:
                pass
            auth.login(request,user)
            messages.success(request,"You are Now logged In")
            return redirect('dashboard')
        else :
            messages.error(request,'Invalid login credentials')
            return redirect('login')
    return render(request,'accounts/login.html')
@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, "Logged out Successfully")
    return redirect('login')

def activate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congrajulations! Your account is activated')
        return redirect('login')
    else:
        messages.warning(request, 'The activation link was broken or has expired. Please register again to create a new account.')
        return redirect('register')
    
@login_required(login_url='login')
def dashboard(request):
    return render(request,'accounts/dashboard.html')
def forgetPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            current_site = get_current_site(request)
            mail_subject = 'Reset your password'
            message = render_to_string('accounts/reset_password_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            messages.success(request,"Password reset link has been sent to "+ email+" ! Click on the link")
            return redirect('login')
        else :
            messages.error(request,'Account does not exists')
            return redirect('forgetPassword')
    return render(request,'accounts/forgetPassword.html')

def resetpassword_validate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password!')
        return redirect('reset-password')
    else:
        messages.warning(request, 'The activation link was broken or has expired. Please register again to create a new account.')
        return redirect('register')
    
def resetpassword(request):
    if request.method == 'POST':
        uid = request.session.get('uid')
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        if password == confirm_password:
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Password has been reset sucessfully')
            return redirect("login")
        else :
            messages.error(request, "Passwords do not match")
            return redirect("reset-password")
    return render(request,'accounts/reset_password.html') 