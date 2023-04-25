from typing import Any, Optional

from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsProject, QgsSettings
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QInputDialog,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QWidget,
)

from askgis.ask_task import AskTask
from askgis.lib.context import compute_context
from askgis.lib.signaling_callback_handler import SignalingCallbackHandler
from askgis.qgis_plugin_tools.tools.custom_logging import add_logger_msg_bar_to_widget
from askgis.qgis_plugin_tools.tools.resources import ui_file_dialog

DialogUi = ui_file_dialog("ask-dialog.ui")  # type: Any


def get_api_key(widget: QWidget):
    auth_mngr = QgsApplication.instance().authManager()
    authid = QgsSettings().value("/AskGIS/authid", None)
    if authid is not None:
        auth = QgsAuthMethodConfig()
        has_auth, _ = auth_mngr.loadAuthenticationConfig(authid, auth, True)
    else:
        has_auth, auth = False, None
    if not has_auth:
        key, ok = QInputDialog.getText(
            widget,
            widget.tr("OpenAI API key"),
            widget.tr("Please enter your OpenAI API key"),
            QLineEdit.PasswordEchoOnEdit,
        )
        if not ok:
            return None
        auth = QgsAuthMethodConfig(method="APIHeader")
        auth.setName("OpenAI API key")
        auth.setConfig("key", key)
        _, auth = auth_mngr.storeAuthenticationConfig(auth)
        QgsSettings().setValue("/AskGIS/authid", auth.id())
    return auth.config("key")


class AskDialog(DialogUi):
    progressBar: QProgressBar
    questionEdit: QLineEdit
    answerEdit: QPlainTextEdit
    logEdit: QPlainTextEdit
    promptEdit: QPlainTextEdit
    codeEdit: QPlainTextEdit
    askBtn: QPushButton
    personalityBox: QComboBox

    def __init__(self, parent: Optional[QWidget]):
        super().__init__(parent)

        add_logger_msg_bar_to_widget(__name__, self)

        self.progressBar.hide()
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(0)

        self.askBtn.clicked.connect(self.ask)
        self.questionEdit.textChanged.connect(self.question_changed)
        self.question_changed()

        # TODO: finish personality setting
        self.personalityBox.hide()

        self._callbacks = SignalingCallbackHandler()
        self._callbacks.text.connect(self.handle_text)
        self._callbacks.chain_start.connect(self.handle_chain_start)
        self._callbacks.chain_end.connect(self.handle_chain_end)
        self._callbacks.tool_end.connect(self.handle_tool_end)
        self._callbacks.agent_action.connect(self.handle_agent_action)
        self._callbacks.agent_finish.connect(self.handle_agent_finish)

        self._task: Optional[AskTask] = None

    def _append_log(self, text: str):
        self.logEdit.setPlainText(self.logEdit.toPlainText() + text)

    def handle_text(self, text: str, kwargs: dict):
        self._append_log(text + kwargs.get("end", ""))

    def handle_chain_start(self, serialized: dict, _inputs: dict):
        self._append_log(f"Entering new {serialized['name']} chain\n")

    def handle_chain_end(self, _outputs: dict):
        self._append_log("Finished chain.\n")

    def handle_tool_end(self, output: str, kwargs: dict):
        self._append_log(
            f"\n{kwargs['observation_prefix']}{output}\n{kwargs['llm_prefix']}"
        )

    def handle_agent_finish(self, _return_values: dict, log: str):
        self._append_log(log + "\n")

    def handle_agent_action(self, _tool: str, _tool_input: str, log: str):
        self._append_log(log)

    def question_changed(self):
        self.askBtn.setEnabled(len(self.questionEdit.text().strip()) > 0)

    def ask(self):
        self.askBtn.setEnabled(False)
        self.questionEdit.setEnabled(False)
        self.codeEdit.clear()
        self.logEdit.clear()

        # region: Get API key

        key = get_api_key(self)
        if key is None:
            self.askBtn.setEnabled(True)
            self.questionEdit.setEnabled(True)
            return

        # endregion

        self.progressBar.show()

        context = compute_context(QgsProject.instance())

        self._task = AskTask(
            self.tr("OpenAI"),
            self.questionEdit.text().strip(),
            context=context,
            api_key=key,
            personality=self.personalityBox.currentText(),
            callbacks=self._callbacks.handler,
        )
        self._task.taskCompleted.connect(self.task_completed)
        self._task.codeChanged.connect(self.codeEdit.setPlainText)
        self._task.promptChanged.connect(self.promptEdit.setPlainText)
        self._task.progressChanged.connect(self.progressBar.setValue)
        QgsApplication.taskManager().addTask(self._task)

    def task_completed(self):
        self.answerEdit.setPlainText(self._task.result.answer)
        self.progressBar.hide()
        self.askBtn.setEnabled(True)
        self.questionEdit.setEnabled(True)
