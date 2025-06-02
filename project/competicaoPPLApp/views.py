from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from pylatex import Document, Section, Math
from pylatex.math import Alignat
from pylatex.utils import NoEscape, escape_latex
from django.core.mail import EmailMessage
from django.contrib import messages
from django.conf import settings
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
    print("--- submit_final called ---")
    sNomeUsuario = request.session.get("sNomeUsuario", "Participante Anônimo") # Default se não estiver na sessão

    if request.method == "POST":
        print(f"--- User: {sNomeUsuario} ---")
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
        
        try:
            nNumeroDicasUtilizadas = int(request.POST.get("quantidade_dicas_usadas", "0"))
        except (ValueError, TypeError):
            nNumeroDicasUtilizadas = 0

        print(f"--- Form Data Retrieved ---")
        print(f"Problema Original: {sProblemaOriginalText[:50]}...") # Print first 50 chars
        print(f"Objetivo: {sObjetivoSelecionado}")
        print(f"Variáveis: {nTotalVariaveisInt}, Restrições: {nTotalRestricoesInt}")

        # Assegurar que os valores sejam pelo menos 1, se aplicável (ou como o formulário de origem os valida)
        nTotalVariaveisInt = max(1, nTotalVariaveisInt)
        nTotalRestricoesInt = max(0, nTotalRestricoesInt) # Pode haver 0 restrições

        # Helper function to format coefficient values for LaTeX display
        def get_display_val_for_latex(value_str_or_float):
            try:
                f_val = float(value_str_or_float)
            except ValueError:
                # Fallback for invalid float string, though form validation should prevent this.
                # Depending on desired behavior, could return "0" or raise error.
                # For LaTeX, returning original string or "0" might be safest.
                return str(value_str_or_float) if isinstance(value_str_or_float, str) else "0"
            
            if f_val == int(f_val):
                return str(int(f_val))
            else:
                # Basic float to string. Consider rounding e.g. "{:.2f}".format(f_val) if needed.
                return str(f_val)

        # Coeficientes da Função Objetivo (c1, c2, ...)
        lCoeficientesObjetivo = []
        for i in range(1, nTotalVariaveisInt + 1):
            lCoeficientesObjetivo.append(request.POST.get(f"c{i}", "0"))
        
        # Operadores entre termos da Função Objetivo (op_obj_1, op_obj_2, ...)
        # Haverá N-1 operadores para N variáveis.
        lOperadoresObjetivo = []
        for i in range(1, nTotalVariaveisInt): # op_obj_1 up to op_obj_{N-1}
            lOperadoresObjetivo.append(request.POST.get(f"op_obj_{i}", "+"))
        
        # Dados das Restrições
        llListaCoeficientesRestricoes = [] 
        llListaOperadoresVarRestricoes = [] 
        lListaOperadoresRelacionaisRestricoesLatex = [] 
        lListaValoresRhsRestricoes = [] 

        for r_idx_form in range(1, nTotalRestricoesInt + 1): # r_idx_form matches form names like r1_c1
            sOpRelRestricao = request.POST.get(f"r{r_idx_form}_rel_op", "<=")
            # Corrected escaping for \leq and \geq to be single backslash in the final string
            # Using if/elif for clarity and to ensure correct assignment
            if sOpRelRestricao == "<=":
                sOpRelRestricaoLatex = "\\leq"
            elif sOpRelRestricao == ">=":
                sOpRelRestricaoLatex = "\\geq"
            elif sOpRelRestricao == "=":
                sOpRelRestricaoLatex = "="
            else:
                sOpRelRestricaoLatex = "\\leq" # Fallback for any unexpected value
            lListaOperadoresRelacionaisRestricoesLatex.append(sOpRelRestricaoLatex)

            lListaValoresRhsRestricoes.append(request.POST.get(f"r{r_idx_form}_rhs", "0"))

            lCoefsEstaRestricao = []
            for v_idx_form in range(1, nTotalVariaveisInt + 1):
                lCoefsEstaRestricao.append(request.POST.get(f"r{r_idx_form}_c{v_idx_form}", "0"))
            llListaCoeficientesRestricoes.append(lCoefsEstaRestricao)

            lOpsVarEstaRestricao = []
            for op_v_idx_form in range(1, nTotalVariaveisInt): # N-1 operadores
                lOpsVarEstaRestricao.append(request.POST.get(f"r{r_idx_form}_op_var_{op_v_idx_form}", "+"))
            llListaOperadoresVarRestricoes.append(lOpsVarEstaRestricao)

        # Construir a string LaTeX para o modelo matemático
        print("--- Constructing LaTeX string for the mathematical model ---")
        partes_latex = []

        # 1. Função Objetivo
        sObjetivoSelecionadoDisplay = sObjetivoSelecionado.capitalize()
        obj_func_str = f"\\text{{{sObjetivoSelecionadoDisplay}}} & ~"
        if nTotalVariaveisInt > 0:
            # Primeiro termo (c1*x1) - User inputs sign directly
            fC1_val_input = float(lCoeficientesObjetivo[0])
            
            if fC1_val_input < 0:
                obj_func_str += f"- {get_display_val_for_latex(abs(fC1_val_input))}x_{{1}}"
            else:
                obj_func_str += f"{get_display_val_for_latex(fC1_val_input)}x_{{1}}"

            # Termos subsequentes (c2*x2, c3*x3, ...)
            for i in range(1, nTotalVariaveisInt): 
                sSelectedOperator = lOperadoresObjetivo[i-1] # Operator from <select> ("+" or "-")
                fCoefInputValue = float(lCoeficientesObjetivo[i])   # Value from <input> (can be pos or neg)

                fEffectiveCoefValue = fCoefInputValue
                if sSelectedOperator == "-":
                    fEffectiveCoefValue *= -1 # Flip sign if operator is minus
                
                # Now, determine the LaTeX string based on the sign of fEffectiveCoefValue
                if fEffectiveCoefValue < 0:
                    obj_func_str += f" - {get_display_val_for_latex(abs(fEffectiveCoefValue))}x_{{{i + 1}}}"
                else: # fEffectiveCoefValue >= 0
                    obj_func_str += f" + {get_display_val_for_latex(fEffectiveCoefValue)}x_{{{i + 1}}}"
        partes_latex.append(obj_func_str)

        # 2. Constraints
        if nTotalRestricoesInt > 0:
            for r_loop_idx in range(nTotalRestricoesInt): # 0 to M-1
                current_constraint_terms_str = ""
                if nTotalVariaveisInt > 0:
                    # Primeiro termo da restrição (r_c1*x1) - User inputs sign directly
                    fR_C1_val_input = float(llListaCoeficientesRestricoes[r_loop_idx][0])
                    
                    if fR_C1_val_input < 0:
                        current_constraint_terms_str += f"- {get_display_val_for_latex(abs(fR_C1_val_input))}x_{{1}}"
                    else:
                        current_constraint_terms_str += f"{get_display_val_for_latex(fR_C1_val_input)}x_{{1}}"

                    # Termos subsequentes da restrição
                    for v_coef_idx in range(1, nTotalVariaveisInt): 
                        sSelectedOperator = llListaOperadoresVarRestricoes[r_loop_idx][v_coef_idx-1]
                        fCoefInputValue = float(llListaCoeficientesRestricoes[r_loop_idx][v_coef_idx])

                        fEffectiveCoefValue = fCoefInputValue
                        if sSelectedOperator == "-":
                            fEffectiveCoefValue *= -1 # Flip sign if operator is minus
                        
                        if fEffectiveCoefValue < 0:
                            current_constraint_terms_str += f" - {get_display_val_for_latex(abs(fEffectiveCoefValue))}x_{{{v_coef_idx + 1}}}"
                        else: # fEffectiveCoefValue >= 0
                            current_constraint_terms_str += f" + {get_display_val_for_latex(fEffectiveCoefValue)}x_{{{v_coef_idx + 1}}}"
                
                sFullConstraintLHS = current_constraint_terms_str.strip()
                sRHS_val_display = get_display_val_for_latex(lListaValoresRhsRestricoes[r_loop_idx])
                # sFullConstraintLine should only be the math part, e.g., "1x_1 + 1x_2 \leq 10"
                sConstraintMathPart = f"{sFullConstraintLHS} {lListaOperadoresRelacionaisRestricoesLatex[r_loop_idx]} {sRHS_val_display}"

                if r_loop_idx == 0: # Primeira restrição
                    # For the first constraint, prepend "\text{Sujeito a:} ~ & "
                    partes_latex.append(f"\\text{{Sujeito a:}} ~ & {sConstraintMathPart}")
                else:
                    # For subsequent constraints, only prepend "& " for alignment
                    partes_latex.append(f"& {sConstraintMathPart}")
            
            # Restrições de não-negatividade (se houver restrições principais)
            if nTotalVariaveisInt > 0:
                sVariaveisNaoNegativas = ", ".join([f"x_{{{j + 1}}}" for j in range(nTotalVariaveisInt)])
                # Corrected escaping for \geq to be single backslash in the final string
                partes_latex.append(f"& {sVariaveisNaoNegativas} \\geq 0")

        sModeloLatex = " \\\\ ".join(partes_latex)
        print(f"--- LaTeX Model String ---")
        print(sModeloLatex)

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

        with doc.create(Section("O problema", numbering=False)):
            if sProblemaOriginalText.strip():
                # Normalize newlines first
                problema_text_normalized = sProblemaOriginalText.replace("\r\n", "\n")
                
                paragraphs = problema_text_normalized.split('\n\n')
                
                for i, para_text in enumerate(paragraphs):
                    escaped_para = escape_latex(para_text)
                    # Handle both typed sequences like ">=" and pasted unicode characters like "≥"
                    math_handled_para = escaped_para.replace(">=", "$\\geq$").replace("≥", "$\\geq$") \
                                                  .replace("<=", "$\\leq$").replace("≤", "$\\leq$")
                    
                    lines_in_para = math_handled_para.split('\n')
                    for k, line_text in enumerate(lines_in_para):
                        doc.append(NoEscape(line_text))
                        if k < len(lines_in_para) - 1:
                            doc.append(NoEscape(r"\\ ")) 
                    
                    if i < len(paragraphs) - 1:
                        doc.append(NoEscape(r"\par")) 
            else:
                 doc.append("Nenhuma descrição do problema fornecida.")

        # Add section for number of hints used
        with doc.create(Section("Informações da Competição", numbering=False)):
            doc.append(f"Número de Dicas Utilizadas: {nNumeroDicasUtilizadas}")

        with doc.create(Section("O modelo", numbering=False)):
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
            print(f"--- Attempting to generate PDF at: {sCaminhoCompletoTexNoExt} ---")
            # Temporarily set clean_tex=False to inspect log files on error
            doc.generate_pdf(sCaminhoCompletoTexNoExt, clean_tex=False, compiler='pdflatex')
            sCaminhoArquivoPdfGerado = f"{sCaminhoCompletoTexNoExt}.pdf"
            print(f"--- PDF generated successfully: {sCaminhoArquivoPdfGerado} ---")
            
            if not os.path.exists(sCaminhoArquivoPdfGerado):
                if os.path.exists(f"{sNomeBaseArquivo}.pdf"):
                    sCaminhoArquivoPdfGerado = f"{sNomeBaseArquivo}.pdf"
                else:
                    raise FileNotFoundError(f"Arquivo PDF não encontrado após a geração: {sCaminhoArquivoPdfGerado} ou {sNomeBaseArquivo}.pdf")

            with open(sCaminhoArquivoPdfGerado, "rb") as f_pdf:
                pdf_bytes = f_pdf.read()
            
            # request.session["download_initiated_flag"] = True # No longer needed for email path

            # Temporarily changed to download PDF instead of emailing - REVERTING THIS
            # print("--- Preparing PDF for download ---")
            # response = HttpResponse(pdf_bytes, content_type="application/pdf")
            # response["Content-Disposition"] = f'attachment; filename="relatorio_ppl_{sNomeUsuario.replace(" ", "_")}.pdf"'
            # print(f"--- Returning PDF download: relatorio_ppl_{sNomeUsuario.replace(' ', '_')}.pdf ---")
            # return response

            # Enable PDF download
            print("--- Preparing PDF for download ---")
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="relatorio_ppl_{sNomeUsuario.replace(" ", "_")}.pdf"'
            print(f"--- Returning PDF download: relatorio_ppl_{sNomeUsuario.replace(' ', '_')}.pdf ---")
            messages.success(request, "Seu relatório foi gerado com sucesso e o download deve iniciar em breve.") # Add a message for the user
            return response

            # Disable email sending logic by commenting it out
            """
            sEmailProfessor = "danieldebrito2105@gmail.com" #"Marco@pucgoias.edu.br" 
            sEmailRemetente = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")

            sAssuntoEmail = f"Relatório Competição PPL - {sNomeUsuario}"
            sCorpoEmail = f"Prezado Professor,\n\nEm anexo, segue o relatório da competição de PPL submetido por {sNomeUsuario}.\n\nAtenciosamente,\nSistema da Competição PPL"

            try:
                print(f"--- Attempting to send email to {sEmailProfessor} from {sEmailRemetente} ---")
                email = EmailMessage(
                    sAssuntoEmail,
                    sCorpoEmail,
                    sEmailRemetente, # From
                    [sEmailProfessor]  # To
                )
                email.attach(f'relatorio_ppl_{sNomeUsuario.replace(" ", "_")}.pdf', pdf_bytes, 'application/pdf')
                email.send()
                messages.success(request, "Seu relatório foi submetido e enviado por e-mail com sucesso!")
                print("--- Email sent successfully! ---")
                # REDIRECT TO THANK YOU PAGE IF EMAIL IS SUCCESSFUL
                # request.session["download_initiated_flag"] = False # Ensure flag is not set for email path
                return redirect("thank_you_page") 
            except Exception as e_email:
                print(f"Erro ao enviar o e-mail: {e_email}")
                messages.error(request, f"Houve um erro ao tentar enviar o e-mail com o relatório: {e_email}. Por favor, entre em contato com o administrador.")
                # Fallback or error handling, could redirect to an error page or back to form with message
                # If email fails, we could offer download as fallback, or redirect to index with error.
                # For now, just redirecting to index with an error message seems reasonable after an email failure.
                return redirect("index") 
            """
            # If emailing was active and successful, we would have redirected.
            # Since we are downloading directly, the return response for download is the end of this request.
            # The redirect("index") below was for the case where email was the main path.
            # return redirect("index") # Original redirect when email was the main path, now handled above

        except Exception as e:
            print(f"Erro ao gerar o PDF: {e}")
            sMensagemErro = f"Ocorreu um erro ao gerar o PDF: {e}. "
            sMensagemErro += "Verifique se o LaTeX está instalado e configurado corretamente no servidor. "
            sMensagemErro += f"Os arquivos temporários do LaTeX foram preservados em: {sDiretorioTemporario} (procure por '{sNomeBaseArquivo}.log'). "
            sMensagemErro += f"Conteúdo LaTeX que tentou ser compilado (para depuração do admin): <pre>{sModeloLatex}</pre>"
            return HttpResponse(sMensagemErro, status=500)
        
        finally:
            # Limpeza dos arquivos temporários - only clean up if PDF was successful and emailed/downloaded
            # If there was an exception during PDF generation, files are kept due to clean_tex=False above
            # and this finally block might not have sCaminhoArquivoPdfGerado properly set if pdf generation failed early.
            
            # We should only clean if sCaminhoArquivoPdfGerado is not empty (meaning PDF generation likely succeeded)
            if sCaminhoArquivoPdfGerado and os.path.exists(sCaminhoArquivoPdfGerado):
                print("--- Cleaning up temporary files after successful PDF handling ---")
                arquivos_para_limpar = [sCaminhoArquivoPdfGerado]
                for ext in ['.tex', '.aux', '.log']:
                    arquivos_para_limpar.append(f"{sCaminhoCompletoTexNoExt}{ext}")
                    arquivos_para_limpar.append(f"{sNomeBaseArquivo}{ext}") # In case CWD was used

                for arquivo in arquivos_para_limpar:
                    if arquivo and os.path.exists(arquivo):
                        try:
                            os.remove(arquivo)
                            print(f"Successfully removed {arquivo}")
                        except OSError as ex_remove:
                            print(f"Erro ao limpar o arquivo temporário {arquivo}: {ex_remove}")
            else:
                print("--- PDF generation or handling failed, temporary files might have been preserved for inspection ---")
    
    else: # GET or other methods
        # Se o nome não estiver na sessão e for um GET, também redirecionar para o index.
        print("--- submit_final called with non-POST method or missing session name ---")
        if not request.session.get("sNomeUsuario"):
            return redirect("index")
        return HttpResponseForbidden("Método não permitido. Por favor, submeta o formulário a partir da Parte 3.")
    

def thank_you_view(request):
    """Displays a thank you page after submission."""
    print("--- thank_you_view called ---")
    sNomeUsuario = request.session.get("sNomeUsuario", "Participante")
    # We can pass a context variable if we want to indicate that a download was part of the process
    # For example, set a session variable in submit_final before redirecting, then check it here.
    # For now, we'll keep it simple.
    context = {
        "sNomeUsuario": sNomeUsuario,
        "download_initiated": request.session.pop("download_initiated_flag", False) # Check and clear a flag
    }
    return render(request, "competicaoPPLApp/thank_you.html", context)
    
