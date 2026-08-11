import numpy as np
import pennylane as qml
import torch

class QuantumService:
    def __init__(self, n_qubits: int = 3):
        self.n_qubits = n_qubits
        # Inicjalizacja wirtualnego urządzenia kwantowego
        self.q_device = qml.device("default.qubit", wires=self.n_qubits)
        
        # Rejestrujemy obwód kwantowy jako QNode powiązany z silnikiem PyTorch
        self.quantum_circuit = qml.QNode(
            self._circuit_definition, 
            self.q_device, 
            interface="torch"
        )

    def _circuit_definition(self, state_vector_input):
        """
        Wewnętrzna definicja obwodu kwantowego (bramki rotacyjne i splatające CNOT).
        """
        for i in range(self.n_qubits):
            qml.RX(state_vector_input[i % len(state_vector_input)], wires=i)
        
        # Splatanie kubitów (Entanglement)
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.CNOT(wires=[2, 0])
        
        # Zwracamy wartość oczekiwaną pomiaru operatora PauliZ dla każdego kubitu
        return [qml.expval(qml.PauliZ(wires=i)) for i in range(self.n_qubits)]

    def get_quantum_style_modifier(self, user_text: str) -> str:
        """
        Przetwarza tekst użytkownika przez stan kwantowy i zwraca modyfikator stylu.
        """
        if not user_text.strip():
            return "Normal"

        # Generujemy stabilny wektor cech (seed) na podstawie tekstu
        seed_input = [len(user_text) * 0.1, np.sin(len(user_text)), 0.5]
        
        with torch.no_grad():
            # Wykonanie obliczeń na symulatorze kwantowym
            q_intent = self.quantum_circuit(seed_input)
            q_intent = torch.stack(q_intent).cpu().numpy()
            
        q_val = float(q_intent[0])
        
        # Klasyfikacja stylu na podstawie wartości kwantowej
        if q_val > 0.2:
            return "Używaj ciekawych, lokalnych idiomów hiszpańskich."
        elif q_val < -0.2:
            return "Zadaj krótkie pytanie niespodziankę na koniec sekcji SPANISH."
        
        return "Normal"

# Eksportujemy gotową instancję serwisu (Wzorzec Singleton)
quantum_service = QuantumService()
