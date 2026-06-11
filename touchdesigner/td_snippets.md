# TouchDesigner - Snippets reutilizables

Codigo reutilizable para tareas comunes en TD y LOPs.

**Ultima revision:** junio 2026.

---

## Listar todos los tools que ve un agente

**Cuando:** al entrar a un proyecto desconocido, o para verificar que tools tiene parseadas un Agent LOP tras cambios en su Tool sequence.

```python
ag = op('/project1/agent_XXX')
n = ag.par.Tool.sequence.numBlocks
print(f"Agent {ag.name}: {n} tool slots, modelo={ag.par.Model.eval()}")
for i in range(n):
    op_par = getattr(ag.par, f'Tool{i}toolop')
    active = getattr(ag.par, f'Tool{i}toolactive')
    tool_op = op_par.eval()
    if tool_op and hasattr(tool_op, 'GetTool'):
        tools = tool_op.GetTool()
        if isinstance(tools, list):
            names = [t.get('tool_definition',{}).get('function',{}).get('name','?') for t in tools]
        elif isinstance(tools, dict):
            names = [tools.get('tool_definition',{}).get('function',{}).get('name','?')]
        else:
            names = ['?']
        print(f"  [{i}] {active.eval()} {tool_op.name} -> {names}")
```

---

## Tester de funcion de modulo en tool_td_mod (sin agente)

**Cuando:** para testear una funcion de un modulo Python en tool_td_mod sin lanzar un agente real (sin coste, sin espera).

```python
import json
tdm = op('/project1/tool_td_mod1')

class MockToolCall:
    def __init__(self, args):
        class _F:
            def __init__(self, a): self.arguments = json.dumps(a)
        self.function = _F(args)

# Listar modulos disponibles
print(tdm.ext.TDModToolEXT.HandleMod(MockToolCall({"action":"list"})))

# Llamar una funcion concreta
result = tdm.ext.TDModToolEXT.HandleMod(MockToolCall({
    "action":"call",
    "function":"<modulo>.<funcion>",
    "args": {"arg1": "valor1"}
}))
print(json.dumps(result, indent=2, default=str))
```

---

## Reset de sesion de un agente sin perder configuracion

**Cuando:** cuando quieres empezar una conversacion limpia con el mismo agente (mismos tools, mismo system_message) sin borrar ni reconfigurar nada.

```python
ag = op('/project1/agent_XXX')
ag.par.Cancelcall.pulse()
ag.par.Clearsession.pulse()
ag.par.reinitextensions.pulse()
# Resultado: conversacion vacia, mismos tools y system_message
```

---

## Cost guard antes de probar nada

**Cuando:** siempre que vayas a lanzar queries de prueba. Pone un tope de gasto duro para que una llamada no se desmande.

```python
ag = op('/project1/agent_test')
ag.par.Costbudget = 0.05  # 5 centimos maximo por query
ag.par.Resetcostmeter.pulse()
# Lanza query; si supera $0.05 el agente corta automaticamente
```
