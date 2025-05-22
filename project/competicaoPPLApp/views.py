from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
# Create your views here.
def index(request):
    # return HttpResponse("Hello, World!")
    return render(request, "competicaoPPLApp/index.html")

def parte1(request):
    """Renders the page for part 1 of the competition."""
    # For now, just render a placeholder template
    return render(request, "competicaoPPLApp/parte1.html")

def parte2(request):
    if request.method == "POST":
        sRespostaProblema = request.POST.get("problema", "")
        if sRespostaProblema == "":
            redirect("parte1")

        return render(request, "competicaoPPLApp/parte2.html", {"sRespostaProblema": sRespostaProblema}) 
        

    return HttpResponseForbidden("Não é possível acessar esta página. Voce deve enviar o formulario da parte 1 antes")

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
        
        try:
            nNumeroDicasUtilizadas = int(request.POST.get("dicas", 0))
        except ValueError:
            nNumeroDicasUtilizadas = 0

        try:
            sRespostaProblema = request.POST.get("problema", "")
        except ValueError:
            sRespostaProblema = ""

        nNumeroDeVariaveis = max(1, nNumeroDeVariaveis)
        nNumeroDeRestricoes = max(1, nNumeroDeRestricoes)

        contexto = {
            "sTipoDeObjetivo": sTipoDeObjetivo,
            "nNumeroDeVariaveis": nNumeroDeVariaveis,
            "nNumeroDeRestricoes": nNumeroDeRestricoes,
            "rangeVariaveis": range(1, nNumeroDeVariaveis + 1),
            "rangeRestricoes": range(1, nNumeroDeRestricoes + 1),
            "nNumeroDicasUtilizadas": nNumeroDicasUtilizadas,
            "sRespostaProblema": sRespostaProblema
        }
        print("dicas ", nNumeroDicasUtilizadas)
        return render(request, "competicaoPPLApp/parte3.html", contexto)
    
    else:
        return HttpResponseForbidden("Não é possível acessar esta página. Voce deve enviar o formulario da parte 2 antes")
    

def submit_final(request):
    if request.method == "POST":
        sRespostaProblema = request.POST.get("problema_original_text")
        sObjetivoSelecionado = request.POST.get("objetivo_selecionado")
        nNumeroTotalVariaveis = request.POST.get("numero_total_variaveis")
        nNumeroTotalRestricoes = request.POST.get("numero_total_restricoes")
        nQuantidadeDicasUsadas = request.POST.get("quantidade_dicas_usadas")

        print("Resposta do problema: ", sRespostaProblema)
        print("Objetivo selecionado: ", sObjetivoSelecionado)
        print("Número total de variáveis: ", nNumeroTotalVariaveis)
    
