import traceback
import sys
from PySide6.QtCore import QRunnable, Slot, Signal, QObject


class WorkerSignals(QObject):
    """
    Define las señales (signals) disponibles para un Worker (hilo de trabajo).    Señales soportadas:
    - finished: No emite datos
    - error: Emite una tupla (Exception, traceback)
    - result: Emite cualquier dato retornado por el procesamiento
    - progress: Emite un entero indicando % de progreso
    """

    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)


class Worker(QRunnable):
    """
    Hereda de QRunnable para manejar configuración, señales y envoltura de ejecución
    para un worker thread (hilo de fondo).
    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()

        # Almacenar argumentos y función a ejecutar
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Agregamos la señal de progreso opcional a kwargs si es necesaria
        # self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        """
        Inicia la ejecución del worker (se llama por QThreadPool).
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Devolvemos el resultado
        finally:
            self.signals.finished.emit()  # Siempre avisamos que terminó
