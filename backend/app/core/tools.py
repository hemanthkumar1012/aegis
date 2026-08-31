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
        return ["refund", "charge", "read"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        # In a real app we'd validate the input schema here based on the action
        if action == "refund" and "amount" not in parameters:
            return {"status": "FAILED", "result": "Amount required for refund"}
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
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class CustomerTool(ToolDefinition):
    @property
    def name(self) -> str:
        return "customer"
        
    @property
    def supported_actions(self) -> List[str]:
        return ["read", "delete"]
        
    def execute(self, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action not in self.supported_actions:
            return {"status": "FAILED", "result": f"Unsupported action {action}"}
        return {"status": "SUCCESS", "result": {"message": f"Processed {action} on {self.name}"}}

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self.register(PaymentTool())
        self.register(DatabaseTool())
        self.register(CustomerTool())
        
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
