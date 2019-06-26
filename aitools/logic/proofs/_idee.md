# Idee sul prover

1. per aggiungere una formula ad una KB dovrebbe bastare scrivere `+formula`
2. le variabili dovrebbero essere generate da un "namespace":
    ```python
    v = VariableNamespace() 
    prover.satisfy(IsA(v.X, cat))
    ```
3. lo stesso dovrebbe valere per le costanti
4. per creare una formula dovrebbe bastare mettere una "f" davanti ad una tupla
5. in alternativa, l'invocazione di un LogicObject dovrebbe creare una formula


In realtà forse basterebbe avere due utilities "variable_source" e "constant_source" che permettono di generarle facilmente.

Dall'altro lato chissene delle costanti, in realtà saranno tutti wrapper!

Quindi partiamo dalla variable_source.