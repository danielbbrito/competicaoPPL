from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from pylatex import Document, Section, Math
from pylatex.math import Alignat
from pylatex.utils import NoEscape
from django.core.mail import EmailMessage
from django.contrib import messages
import os
import tempfile
import uuid

def index(request):
    sMensagemErro = None
    if request.method == "POST":
        sNomeUsuario = request.POST.get("sNomeUsuario", "").strip()
        if sNomeUsuario:
            request.session["sNomeUsuario"] = sNomeUsuario
            return redirect("parte1")
        else:
            sMensagemErro = "Por favor, insira seu nome para continuar."
    return render(request, "competicaoPPLApp/index.html", {"sMensagemErro": sMensagemErro})

def parte1(request):
    """Renders the page for part 1 of the competition."""
    sNomeUsuario = request.session.get("sNomeUsuario")
    if not sNomeUsuario:
        # Adicionar uma mensagem flash aqui seria o ideal, mas por simplicidade vamos redirecionar.
        # Para mensagens flash: from django.contrib import messages; messages.error(request, "Por favor, insira seu nome.")
        return redirect("index")

    # For now, just render a placeholder template
    return render(request, "competicaoPPLApp/parte1.html", {"sNomeUsuario": sNomeUsuario})

def parte2(request):
    sNomeUsuario = request.session.get("sNomeUsuario")
    if not sNomeUsuario:
        return redirect("index")

    if request.method == "POST":
        sProblema = request.POST.get("problema", "")
        if sProblema == "":
            # Idealmente, passar sNomeUsuario de volta se a validação falhar e quisermos ficar na mesma página com erro
            return redirect("parte1") # Ou renderizar parte1 com erro

        return render(request, "competicaoPPLApp/parte2.html", {"sProblema": sProblema, "sNomeUsuario": sNomeUsuario})
        
    return HttpResponseForbidden("Não é possível acessar esta página diretamente. Você deve enviar o formulário da parte 1 antes ou o seu nome não foi fornecido.")

def parte3(request):
    sNomeUsuario = request.session.get("sNomeUsuario")
    if not sNomeUsuario:
        return redirect("index")

    if request.method == "POST":
        try:
            nObjetivoInt = int(request.POST.get("objetivo", 1)) 
        except ValueError:
            nObjetivoInt = 1 
        
        # 1 é minimizar, 0 é maximizar
        sTipoDeObjetivo = "minimizar" if nObjetivoInt == 1 else "maximizar"
        
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
            sProblema = request.POST.get("problema", "")
        except ValueError:
            sProblema = ""

        nNumeroDeVariaveis = max(1, nNumeroDeVariaveis)
        nNumeroDeRestricoes = max(1, nNumeroDeRestricoes)

        contexto = {
            "sTipoDeObjetivo": sTipoDeObjetivo,
            "nNumeroDeVariaveis": nNumeroDeVariaveis,
            "nNumeroDeRestricoes": nNumeroDeRestricoes,
            "rangeVariaveis": range(1, nNumeroDeVariaveis + 1),
            "rangeRestricoes": range(1, nNumeroDeRestricoes + 1),
            "nNumeroDicasUtilizadas": nNumeroDicasUtilizadas,
            "sProblema": sProblema,
            "sNomeUsuario": sNomeUsuario
        }
        print(contexto)
        
        return render(request, "competicaoPPLApp/parte3.html", contexto)
    
    else:
        return HttpResponseForbidden("Não é possível acessar esta página diretamente. Voce deve enviar o formulario da parte 2 antes ou o seu nome não foi fornecido.")
    

def submit_final(request):
    sNomeUsuario = request.session.get("sNomeUsuario", "Participante Anônimo") # Default se não estiver na sessão

    if request.method == "POST":
        sProblemaOriginalText = request.POST.get("problema_original_text", "")
        sObjetivoSelecionado = request.POST.get("objetivo_selecionado", "minimizar")
        
        try:
            nTotalVariaveisInt = int(request.POST.get("numero_total_variaveis", "2"))
        except (ValueError, TypeError):
            nTotalVariaveisInt = 2 
        
        try:
            nTotalRestricoesInt = int(request.POST.get("numero_total_restricoes", "2"))
        except (ValueError, TypeError):
            nTotalRestricoesInt = 2

        # Assegurar que os valores sejam pelo menos 1, se aplicável (ou como o formulário de origem os valida)
        nTotalVariaveisInt = max(1, nTotalVariaveisInt)
        nTotalRestricoesInt = max(0, nTotalRestricoesInt) # Pode haver 0 restrições

        # Coeficientes da Função Objetivo (c1, c2, ...)
        lCoeficientesObjetivo = []
        for i in range(nTotalVariaveisInt):
            lCoeficientesObjetivo.append(request.POST.get(f"c{i + 1}", "0"))
        
        # Operadores entre termos da Função Objetivo (op_obj_1, op_obj_2, ...)
        lOperadoresObjetivo = []
        for i in range(nTotalVariaveisInt - 1):
            lOperadoresObjetivo.append(request.POST.get(f"op_obj_{i + 1}", "+"))
        
        # Dados das Restrições
        llListaCoeficientesRestricoes = [] 
        llListaOperadoresVarRestricoes = [] 
        lListaOperadoresRelacionaisRestricoesLatex = [] 
        lListaValoresRhsRestricoes = [] 

        for r_idx in range(1, nTotalRestricoesInt + 1):
            # Coeficientes para a restrição r_idx (r{r_idx}_c{v_idx})
            lCoefsEstaRestricao = []
            for v_idx in range(1, nTotalVariaveisInt + 1):
                lCoefsEstaRestricao.append(request.POST.get(f"r{r_idx}_c{v_idx}", "0"))
            llListaCoeficientesRestricoes.append(lCoefsEstaRestricao)

            # Operadores entre variáveis para a restrição r_idx (r{r_idx}_op_var{op_v_idx})
            lOpsVarEstaRestricao = []
            for op_v_idx in range(1, nTotalVariaveisInt): # N-1 operadores para N termos
                lOpsVarEstaRestricao.append(request.POST.get(f"r{r_idx}_op_var_{op_v_idx}", "+"))
            llListaOperadoresVarRestricoes.append(lOpsVarEstaRestricao)
            
            sOpRelRestricao = request.POST.get(f"r{r_idx}_rel_op", "<=")
            sOpRelRestricaoLatex = sOpRelRestricao.replace("<=", "\\leq").replace(">=", "\\geq").replace("=", "=")
            # Fallback if not a known operator - though form should limit choices
            if sOpRelRestricaoLatex not in ["\\leq", "\\geq", "="]:
                sOpRelRestricaoLatex = "\\leq"
            lListaOperadoresRelacionaisRestricoesLatex.append(sOpRelRestricaoLatex)

            lListaValoresRhsRestricoes.append(request.POST.get(f"r{r_idx}_rhs", "0"))

        # Construir a string LaTeX para o modelo matemático
        partes_latex = []

        # 1. Função Objetivo
        # User wants to remove Z = but keep alignment for the expression itself.
        # "Minimizar" will be on the left, then an alignment point, then the expression.
        obj_func_str = "\\text{" + sObjetivoSelecionado + "} & ~" # Add & for alignment after the text
        for i in range(nTotalVariaveisInt):
            obj_func_str += f"{lCoeficientesObjetivo[i]}x_{{{i + 1}}}"
            if i < nTotalVariaveisInt - 1:
                obj_func_str += f" {lOperadoresObjetivo[i]} "
        partes_latex.append(obj_func_str)

        # 2. Constraints (incluindo "sujeito a:") e Não-negatividade
        if nTotalRestricoesInt > 0:
            # Primeira restrição com "sujeito a:"
            first_constraint_text_part = "\\text{sujeito a:} ~"
            # Construir a parte da equação da primeira restrição
            first_constraint_eq_part = ""
            for v_idx in range(nTotalVariaveisInt):
                first_constraint_eq_part += f"{llListaCoeficientesRestricoes[0][v_idx]}x_{{{v_idx + 1}}}"
                if v_idx < nTotalVariaveisInt - 1:
                    first_constraint_eq_part += f" {llListaOperadoresVarRestricoes[0][v_idx]} "
            first_constraint_eq_part += f" {lListaOperadoresRelacionaisRestricoesLatex[0]} {lListaValoresRhsRestricoes[0]}"
            partes_latex.append(f"{first_constraint_text_part} & {first_constraint_eq_part}")

            # Restrições subsequentes
            for r_idx in range(1, nTotalRestricoesInt):
                constraint_str = "& " # Apenas o marcador de alinhamento e a equação
                for v_idx in range(nTotalVariaveisInt):
                    constraint_str += f"{llListaCoeficientesRestricoes[r_idx][v_idx]}x_{{{v_idx + 1}}}"
                    if v_idx < nTotalVariaveisInt - 1:
                        constraint_str += f" {llListaOperadoresVarRestricoes[r_idx][v_idx]} "
                constraint_str += f" {lListaOperadoresRelacionaisRestricoesLatex[r_idx]} {lListaValoresRhsRestricoes[r_idx]}"
                partes_latex.append(constraint_str)
            
            # Restrições de não-negatividade (se houver restrições principais)
            if nTotalVariaveisInt > 0:
                sVariaveisNaoNegativas = ", ".join([f"x_{{{j + 1}}}" for j in range(nTotalVariaveisInt)])
                partes_latex.append(f"& {sVariaveisNaoNegativas} \\geq 0")

        elif nTotalVariaveisInt > 0: # Sem restrições principais, apenas não-negatividade
            sVariaveisNaoNegativas = ", ".join([f"x_{{{j + 1}}}" for j in range(nTotalVariaveisInt)])
            # Para alinhar com o Z &= ..., esta também precisa de um &
            # Poderíamos adicionar um "tal que" ou similar se quiséssemos texto aqui.
            partes_latex.append(f"& {sVariaveisNaoNegativas} \\geq 0")
        
        sModeloLatex = " \\\\ ".join(partes_latex)

        geometry_options = {
            "tmargin": "2cm",
            "lmargin": "2cm",
            "rmargin": "2cm",
            "bmargin": "2cm"
        }
        doc = Document(geometry_options=geometry_options)

        # Adicionar nome do usuário e título ao PREAMBLE do PDF
        doc.preamble.append(NoEscape(r'\title{Relatório de Problema de Programação Linear}'))
        doc.preamble.append(NoEscape(f'\\author{{{sNomeUsuario}}}'))
        doc.preamble.append(NoEscape(r'\date{\today}'))
        
        # \maketitle DEVE vir DEPOIS de \begin{document}
        # pylatex insere \begin{document} implicitamente quando o primeiro conteúdo do corpo é adicionado.
        # Portanto, adicionamos \maketitle como o primeiro item no corpo do documento.
        doc.append(NoEscape(r'\maketitle'))

        with doc.create(Section("O problema")):
            doc.append(sProblemaOriginalText if sProblemaOriginalText else "Nenhuma descrição do problema fornecida.")

        with doc.create(Section("O modelo")):
            if sModeloLatex.strip():
                try:
                    with doc.create(Alignat(numbering=False)) as agn:
                        agn.append(NoEscape(sModeloLatex))
                except Exception as e_pylatex_construct:
                    return HttpResponse(f"Erro interno do PyLaTeX ao construir o modelo matemático: {e_pylatex_construct}", status=500)
            else:
                doc.append("Modelo matemático não pôde ser construído (verifique o número de variáveis).")

        # Gerar PDF em um diretório temporário
        sNomeBaseArquivo = f"relatorio_ppl_{uuid.uuid4().hex}"
        sDiretorioTemporario = tempfile.gettempdir()
        sCaminhoCompletoTexNoExt = os.path.join(sDiretorioTemporario, sNomeBaseArquivo)
        
        sCaminhoArquivoPdfGerado = ""

        try:
            doc.generate_pdf(sCaminhoCompletoTexNoExt, clean_tex=True, compiler='pdflatex')
            sCaminhoArquivoPdfGerado = f"{sCaminhoCompletoTexNoExt}.pdf"
            
            if not os.path.exists(sCaminhoArquivoPdfGerado):
                if os.path.exists(f"{sNomeBaseArquivo}.pdf"):
                    sCaminhoArquivoPdfGerado = f"{sNomeBaseArquivo}.pdf"
                else:
                    raise FileNotFoundError(f"Arquivo PDF não encontrado após a geração: {sCaminhoArquivoPdfGerado} ou {sNomeBaseArquivo}.pdf")

            with open(sCaminhoArquivoPdfGerado, "rb") as f_pdf:
                pdf_bytes = f_pdf.read()
            
            # Em vez de retornar o PDF como download, vamos enviá-lo por e-mail
            sEmailProfessor = "professor@example.com"  # <<< COLOQUE O E-MAIL DO PROFESSOR AQUI
            sEmailRemetente = "noreply@example.com" # <<< COLOQUE UM REMETENTE VÁLIDO OU CONFIGURE DEFAULT_FROM_EMAIL

            sAssuntoEmail = f"Relatório Competição PPL - {sNomeUsuario}"
            sCorpoEmail = f"Prezado Professor,\n\nEm anexo, segue o relatório da competição de PPL submetido por {sNomeUsuario}.\n\nAtenciosamente,\nSistema da Competição PPL"

            try:
                email = EmailMessage(
                    sAssuntoEmail,
                    sCorpoEmail,
                    sEmailRemetente, # From
                    [sEmailProfessor]  # To
                )
                email.attach(f'relatorio_ppl_{sNomeUsuario.replace(" ", "_")}.pdf', pdf_bytes, 'application/pdf')
                email.send()
                messages.success(request, "Seu relatório foi submetido e enviado por e-mail com sucesso!")
            except Exception as e_email:
                print(f"Erro ao enviar o e-mail: {e_email}")
                messages.error(request, f"Houve um erro ao tentar enviar o e-mail com o relatório: {e_email}. Por favor, entre em contato com o administrador.")
                # Opcional: Poderia retornar o PDF para download como fallback se o e-mail falhar
                # response = HttpResponse(pdf_bytes, content_type="application/pdf")
                # response["Content-Disposition"] = f'attachment; filename="relatorio_ppl_{sNomeUsuario.replace(" ", "_")}.pdf"'
                # return response

            return redirect("index") # Redirecionar para a página inicial (ou outra de sucesso)

        except Exception as e:
            print(f"Erro ao gerar o PDF: {e}")
            sMensagemErro = f"Ocorreu um erro ao gerar o PDF: {e}. "
            sMensagemErro += "Verifique se o LaTeX está instalado e configurado corretamente no servidor. "
            sMensagemErro += f"Conteúdo LaTeX que tentou ser compilado (para depuração do admin): <pre>{sModeloLatex}</pre>"
            return HttpResponse(sMensagemErro, status=500)
        
        finally:
            # Limpeza dos arquivos temporários
            arquivos_para_limpar = [sCaminhoArquivoPdfGerado]
            for ext in ['.tex', '.aux', '.log']:
                arquivos_para_limpar.append(f"{sCaminhoCompletoTexNoExt}{ext}")
                # Caso o arquivo tenha sido gerado no CWD por algum motivo
                arquivos_para_limpar.append(f"{sNomeBaseArquivo}{ext}")


            for arquivo in arquivos_para_limpar:
                if arquivo and os.path.exists(arquivo):
                    try:
                        os.remove(arquivo)
                    except OSError as ex_remove:
                        print(f"Erro ao limpar o arquivo temporário {arquivo}: {ex_remove}")
    
    else: # GET or other methods
        # Se o nome não estiver na sessão e for um GET, também redirecionar para o index.
        if not request.session.get("sNomeUsuario"):
            return redirect("index")
        return HttpResponseForbidden("Método não permitido. Por favor, submeta o formulário a partir da Parte 3.")
    
