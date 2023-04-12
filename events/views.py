from django.shortcuts import render, redirect
import calendar
from calendar import HTMLCalendar
from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from .models import Event, Venue
from .forms import VenueForm, EventForm, EventFormAdmin
from django.db.models import Q
from django.db.models.functions import Lower
from django.contrib import messages
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from django.core.paginator import Paginator
from django.contrib.auth.models import User

# Create your views here.


def my_events(request):
    if request.user.is_authenticated:
        me = request.user.id
        events = Event.objects.filter(manager=me)
        return render(request, 'events/my_event.html', { "me":me, "events":events })
    else:
        messages.success(request, ("You're not auhorised to access this page."))
        return redirect('home')


def venue_pdf(request):

    buf = io.BytesIO()

    c = canvas.Canvas(buf, pagesize=letter, bottomup=0)

    textob = c.beginText()
    textob.setTextOrigin(inch, inch)
    textob.setFont("Helvetica", 14)

    # lines = [
    #     "This is line 1",
    #     "This is line 2",
    #     "This is line 3",
    #     "This is line 4",
    # ]

    venues = Venue.objects.all()

    lines = []

    for venue in venues:
        lines.append(venue.name)
        lines.append(venue.address)
        lines.append(venue.zip_code)
        lines.append(venue.phone)
        lines.append(venue.web)
        lines.append(venue.email_address)
        lines.append(" ")


    for line in lines:
        textob.textLine(line)

    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)

    return FileResponse(buf, as_attachment=True, filename="venues.pdf")


def venue_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename=venues.csv'

    writer = csv.writer(response)

    venues = Venue.objects.all()

    writer.writerow(['Venue Name', 'Address', 'Zip Code', 'Phone', 'Web', 'Email Address'])

    for venue in venues:
        writer.writerow([venue.name, venue.address, venue.zip_code, venue.phone, venue.web, venue.email_address])

    return response


def venue_text(request):
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition']='attachment; filename=venues.txt'
    venues = Venue.objects.all()

    lines = []

    for venue in venues:
        lines.append(f'--{venue.name}\n--{venue.address}\n--{venue.zip_code}\n--{venue.phone}\n--{venue.web}\n--{venue.email_address}\n\n')
    
    response.writelines(lines)
    return response
    


def delete_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue.delete()
    messages.warning(request, ("Venue has been successfully deleted!"))
    return redirect('list-venues')


def delete_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.user == event.manager:
        event.delete()
        messages.success(request, ("Event Deleted!"))
        return redirect('list-events')
    else:
        messages.success(request, ("You are not allowed to delete this event."))
        return redirect('list-events')


def update_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.user.is_superuser:
        form = EventFormAdmin(request.POST or None, instance=event)
    else:
        form = EventForm(request.POST or None, instance=event)

    if form.is_valid():
        form.save()
        return redirect('list-events')
    
    return render(request, 'events/update_event.html', { 'event':event, 'form':form })


def add_event(request):

    submitted = False
    if request.method == "POST":
        if request.user.is_superuser:
            form = EventFormAdmin(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('add_event?submitted=True')
            
        else:
            form = EventForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.manager = request.user
                event.save()
                return HttpResponseRedirect('add_event?submitted=True')

    else:
        if request.user.is_superuser:
            form = EventFormAdmin
        else:
            form = EventForm
        if 'submitted' in request.GET:
            submitted = True
        return render(request, 'events/add_event.html', { 'form':form, 'submitted':submitted })
    

def update_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    form = VenueForm(request.POST or None, instance=venue)
    if form.is_valid():
        form.save()
        return redirect('list-venues')
    
    else:
        return render(request, 'events/update_venue.html', { 'venue': venue, 'form':form })


def search_venues(request):
    
    if request.method == "POST":
        searched = request.POST['searched']
        venues = Venue.objects.filter(Q(name__contains=searched)|
                                      Q(address__contains=searched)|
                                      Q(zip_code__contains=searched))
        return render(request, 'events/search_venues.html', { 'searched': searched, 'venues':venues })
    
    else:
        return render(request, 'events/search_venues.html', {})
    

def search_events(request):
    
    if request.method == "POST":
        searched = request.POST['searched']
        events = Event.objects.filter(name__contains=searched)
        return render(request, 'events/search_events.html', { 'searched': searched, 'events':events })
    
    else:
        return render(request, 'events/search_events.html', {})
    

def show_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue_owner = User.objects.get(pk=venue.owner)
    return render(request, 'events/show_venue.html', { 'venue': venue, 'venue_owner': venue_owner })


def list_venues(request):
    venue_list = Venue.objects.all().order_by(Lower('name'))

    # Set up pagination.
    p = Paginator(Venue.objects.all(), 2)
    page = request.GET.get('page')
    venues = p.get_page(page)
    nums = "a" * venues.paginator.num_pages

    return render(request, 'events/venue.html', { 'venue_list':venue_list, 'venues':venues, 'nums':nums })


def add_venue(request):

    submitted = False
    if request.method == "POST":
        form = VenueForm(request.POST)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.owner = request.user.id
            venue.save()
        return HttpResponseRedirect('add_venue?submitted=True')

    else:
        form = VenueForm
        if 'submitted' in request.GET:
            submitted = True
        return render(request, 'events/add_venue.html', { 'form':form, 'submitted':submitted })
    

def all_events(request):
    event_list = Event.objects.all().order_by('-event_date')
    return render(request, 'events/event_list.html', { 'event_list':event_list })
    

def home(request, year=datetime.now().year, month=datetime.now().strftime('%B')):
    name = "Jhon"

    month = month.capitalize()
    month_number = list(calendar.month_name).index(month)
    month_number = int(month_number)

    cal = HTMLCalendar().formatmonth(year, month_number)

    now = datetime.now()
    current_year = now.year

    time = now.strftime('%I:%M %p')

    # query the event model for dates
    event_list = Event.objects.filter(event_date__year=year, event_date__month=month_number)

    return render(request, 'events/home.html', { "name": name, "year": year, "month": month, "month_number": month_number, "cal": cal,
                                                "current_year": current_year, "time": time, "event_list":event_list })
