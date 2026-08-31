from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ToolDefinition(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def supported_actions(self) -> List[str]:
        pass
        
    @abstractmethod
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        pass

class PaymentTool(ToolDefinition):
    @property
    def name(self) -> str:
        return "payment"
        
    @property
    def supported_actions(self) -> List[str]:
        return ["read", "refund", "charge"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        if action in ["refund", "charge"] and "amount" not in parameters:
            return {"status": "FAILED", "result": "Amount required for transaction"}
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class DatabaseTool(ToolDefinition):
    @property
    def name(self) -> str:
        return "database"
        
    @property
    def supported_actions(self) -> List[str]:
        return ["read", "write", "export", "delete"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        if action == "write" and "data" not in parameters:
            return {"status": "FAILED", "result": "Data required for write"}
        if action == "export" and "destination" not in parameters:
            return {"status": "FAILED", "result": "Destination required for export"}
        if action == "delete" and "record_id" not in parameters:
            return {"status": "FAILED", "result": "Record ID required for delete"}
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class CustomerTool(ToolDefinition):
    @property
    def name(self) -> str:
        return "customer"
        
    @property
    def supported_actions(self) -> List[str]:
        return ["read", "update", "delete"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        if action == "update" and "fields" not in parameters:
            return {"status": "FAILED", "result": "Fields required for update"}
        if action == "delete" and "customer_id" not in parameters:
            return {"status": "FAILED", "result": "Customer ID required for delete"}
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class TicketTool(ToolDefinition):
    @property
    def name(self) -> str:
        return "ticket"
        
    @property
    def supported_actions(self) -> List[str]:
        return ["read", "update", "close"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        if action == "update" and "fields" not in parameters:
            return {"status": "FAILED", "result": "Fields required for update"}
        if action == "close" and "reason" not in parameters:
            return {"status": "FAILED", "result": "Reason required for close"}
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class EmailTool(ToolDefinition):
    @property
    def name(self) -> str:
        return "email"
        
    @property
    def supported_actions(self) -> List[str]:
        return ["draft", "send"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        if "recipient" not in parameters or "body" not in parameters:
            return {"status": "FAILED", "result": "Recipient and body required for email"}
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class DeploymentTool(ToolDefinition):
    @property
    def name(self) -> str:
        return "deployment"
        
    @property
    def supported_actions(self) -> List[str]:
        return ["read", "deploy", "rollback"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        if action in ["deploy", "rollback"] and "version" not in parameters:
            return {"status": "FAILED", "result": "Version required for deployment actions"}
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self.register(PaymentTool())
        self.register(DatabaseTool())
        self.register(CustomerTool())
        self.register(TicketTool())
        self.register(EmailTool())
        self.register(DeploymentTool())
        
    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool
        
    def execute(self, tool_name: str, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        tool = self._tools.get(tool_name)
        if not tool:
            return {"status": "FAILED", "result": f"Unknown tool: {tool_name}"}
            
        try:
            return tool.execute(action, resource, parameters)
        except Exception as e:
            # Prevent arbitrary exceptions from leaking
            return {"status": "FAILED", "result": "Internal execution error"}

registry = ToolRegistry()
