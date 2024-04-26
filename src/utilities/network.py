# NETWORKING IP/PORTS #
SERVER_IPV4 = "127.0.0.1"   # communication center's IPV4
MOBILE_PORT = 2501          # Mobile     controller service port
MULTIM_PORT = 2502          # Multimedia controller service port
MOUSET_PORT = 2503          # Mouse-Trap controller service port

# NETWORKING SERVERS/CLIENTS #
MOBILE_SERVER = "MOBILE-SRVR"
MOBILE_CLIENT = "MOBILE-CLNT"
MULTIM_SERVER = "MULTIM-SRVR"
MULTIM_CLIENT = "MULTIM-CLNT"
MOUSET_SERVER = "MOUSET-SRVR"
MOUSET_CLIENT = "MOUSET-CLNT"

def service_port(service):
    match service:
        case MOBILE_SERVICE if MOBILE_SERVICE == MOBILE_SERVER or MOBILE_SERVICE == MOBILE_CLIENT:
            return MOBILE_PORT
        case MULTIM_SERVICE if MULTIM_SERVICE == MULTIM_SERVER or MULTIM_SERVICE == MULTIM_CLIENT:
            return MULTIM_PORT
        case MOUSET_SERVICE if MOUSET_SERVICE == MOUSET_SERVER or MOUSET_SERVICE == MOUSET_CLIENT:
            return MOUSET_PORT
        case _: raise RuntimeError(f"service={service} not supported!")