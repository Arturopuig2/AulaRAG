import requests

url = "http://127.0.0.1:8000/chat"
data = {"message": "[Contexto: asignatura actual es Lengua] Ponme un ejemplo visual con botones para adivinar si camión es aguda llana o esdrújula"}
response = requests.post(url, data=data)

print(response.json())

data2 = {"message": "[Contexto: asignatura actual es Lengua] Esdrújula"}
response2 = requests.post(url, data=data2)

print("\n\nRESPONSE 2:\n", response2.json())
