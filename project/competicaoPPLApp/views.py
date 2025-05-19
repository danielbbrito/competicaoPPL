from django.shortcuts import render, redirect
from django.http import HttpResponse
# Create your views here.
def index(request):
    # return HttpResponse("Hello, World!")
    return render(request, "competicaoPPLApp/index.html")

def parte1(request):
    """Renders the page for part 1 of the competition."""
    # For now, just render a placeholder template
    return render(request, "competicaoPPLApp/parte1.html")

def parte2(request):
    return render(request, "competicaoPPLApp/parte2.html")

def parte3(request):
    if request.method == "POST":
        try:
            nObjetivoInt = int(request.POST.get("objetivo", 1)) # Default to 1 (maximizar) based on new logic
        except ValueError:
            nObjetivoInt = 1 # Default if conversion fails
        
        # User's logic: 0 for minimizar, 1 (or other) for maximizar
        sTipoDeObjetivo = "minimizar" if nObjetivoInt == 0 else "maximizar"

        try:
            nNumeroDeVariaveis = int(request.POST.get("variaveis", 2))
        except ValueError:
            nNumeroDeVariaveis = 2
        
        try:
            nNumeroDeRestricoes = int(request.POST.get("restricoes", 2))
        except ValueError:
            nNumeroDeRestricoes = 2
        
        nNumeroDeVariaveis = max(1, nNumeroDeVariaveis)
        nNumeroDeRestricoes = max(1, nNumeroDeRestricoes)

        contexto = {
            "sTipoDeObjetivo": sTipoDeObjetivo,
            "nNumeroDeVariaveis": nNumeroDeVariaveis,
            "nNumeroDeRestricoes": nNumeroDeRestricoes,
            "rangeVariaveis": range(1, nNumeroDeVariaveis + 1),
            "rangeRestricoes": range(1, nNumeroDeRestricoes + 1)
        }
        return render(request, "competicaoPPLApp/parte3.html", contexto)
    
    contexto = {
        "sTipoDeObjetivo": "maximizar", # Default for GET
        "nNumeroDeVariaveis": 2,
        "nNumeroDeRestricoes": 2,
        "rangeVariaveis": range(1, 3),
        "rangeRestricoes": range(1, 3)
    }
    return render(request, "competicaoPPLApp/parte3.html", contexto)

    
    
