from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Create your views here.


def logout_user(request):
    logout(request)
    messages.success(request, ("You have logout successfully."))
    return redirect('home')


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ("login where successfull."))
            # Redirect to a success page.
            return redirect('home')
            ...
        else:
            messages.success(request, ("There was an error logging in. Try again"))
            # Return an 'invalid login' error message.
            return redirect('login')
            ...

    else:
        return render(request, 'authenticate/login.html', {})
