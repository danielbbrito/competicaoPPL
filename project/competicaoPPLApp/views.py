from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def index(request):
    # return HttpResponse("Hello, World!")
    return render(request, "competicaoPPLApp/index.html")

def parte1(request):
    """Renders the page for part 1 of the competition."""
    # For now, just render a placeholder template
    return render(request, "competicaoPPLApp/parte1.html")

def part2(request):
    return render(request, "competicaoPPLApp/parte2.html")
