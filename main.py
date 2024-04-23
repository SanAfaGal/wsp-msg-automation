import subprocess as sb
import time
from tkinter import messagebox
from urllib.parse import quote

import pyautogui as pg
from pywhatkit.core import core, exceptions, log

from data import get_info_of_customers, filter_data_by_vendor

CHROME_PATH = f'C:/Program Files/Google/Chrome/Application/chrome.exe'
EDGE_PATH = f'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
WAIT_TIME_PER_CUSTOMER: int = 15  # Time to wait before sending the message
CLOSE_TAB_WAIT_TIME: int = 2  # Time to wait before closing the tab


def send_wsp_msg(
        phone_number: str,
        message: str,
        close_tab_after_send: bool = False,
        browser_path: str = EDGE_PATH
) -> None:
    """
    Send WhatsApp message instantly.

    Args:
        phone_number (str): The phone number to send the message to.
        message (str): The message content.
        close_tab_after_send (bool): Whether to close the browser tab after sending the message, default is False.
        browser_path (str): Path to the browser executable, default is EDGE.

    Raises:
        exceptions.CountryCodeException: If country code is missing in the phone number.
    """

    if not core.check_number(number=phone_number):
        raise exceptions.CountryCodeException("Country Code Missing in Phone Number!")

    # Construct the URL for sending a WhatsApp message using the provided phone number and message content
    url = f"https://web.whatsapp.com/send?phone={phone_number}&text={quote(message)}"
    # Open the specified browser with the constructed URL
    sb.Popen([browser_path, url])
    # Wait for 4 seconds to ensure the WhatsApp Web page is fully loaded
    time.sleep(4)
    # Click at the center of the screen to focus on the message input area in the WhatsApp Web interface
    pg.click(core.WIDTH / 2, core.HEIGHT / 2)
    # Wait for the specified time (minus 4 seconds) before sending the message
    time.sleep(WAIT_TIME_PER_CUSTOMER - 4)
    # Simulate pressing the 'Enter' key to send the message
    pg.press("enter")
    # Log the sent message along with the current timestamp, receiver's phone number, and message content
    log.log_message(_time=time.localtime(), receiver=phone_number, message=message)

    if close_tab_after_send:
        core.close_tab(wait_time=CLOSE_TAB_WAIT_TIME)


def send_messages_to_customers(customers: list[dict[str, str]], browser: str) -> None:
    """
    Send messages to a list of customers.

    Args:
        customers (List[Dict[str, str]): Dictionary containing customer information.
        browser (str): Path to the browser executable.
    """

    for customer in customers:
        send_wsp_msg(customer['TELEFONO'], customer['MENSAJE'], close_tab_after_send=True, browser_path=browser)
        print(f"Message sent to {customer['CLIENTE']} → OK")


def calculate_total_time(*customer_lists: list[dict[str, str]]) -> int:
    """
    Calculate the total time required to send messages to all customers.

    Args:
        *customer_lists (list[dict[str, str]]): Lists of customers.

    Returns:
        int: Total time in seconds required to send messages to all customers.
    """
    number_of_customers = sum(len(customers) for customers in customer_lists)
    time_per_customer = WAIT_TIME_PER_CUSTOMER + CLOSE_TAB_WAIT_TIME
    return number_of_customers * time_per_customer


def show_confirmation_dialog(n_customers: int, time_expected_secs: int) -> bool:
    """
    Show a confirmation dialog with the estimated time and ask the user to continue or cancel.

    Args:
        n_customers (int): Number of customers.
        time_expected_secs (int): Total time in seconds.

    Returns:
        bool: True if the user chooses to continue, False otherwise.
    """
    minutes = time_expected_secs // 60
    seconds = time_expected_secs % 60
    message = (f"Clientes: {n_customers} \n"
               f"Tiempo estimado: {minutes} minutos y {seconds} segundos")
    result = messagebox.askyesno("Confirmación", message)
    return result


def show_end_dialog() -> str:
    """
    Display an end-of-program notification dialog.

    Returns:
    str: A string indicating that the program has finished.
    """
    return messagebox.showinfo("Notificación", "El programa ha finalizado.")


def print_customers(vendor: str, dict_customer: list[dict]):
    """
    Print customer information for a specific vendor.

    Args:
    vendor (str): The initials of the vendor.
    dict_customer (list[dict]): A list of dictionaries containing customer information.

    Returns:
    None
    """
    print(f"VENDEDOR: {vendor}".center(17, '*'))

    for i, customer in enumerate(dict_customer, start=1):
        print(f"{i}) CLIENTE: {customer['CLIENTE']} - MENSAJE: {customer['MENSAJE']}")

    print()


# Obtain customers for Edge and Chrome browsers
df_customers = get_info_of_customers('0', 'Hoy', '1', 'Mañana')

vendor_initials_edge = 'BGL'
vendor_initials_chrome = 'SAG'

# Filter customers by vendor
customers_edge = filter_data_by_vendor(vendor_initials_edge, df_customers)
customers_chrome = filter_data_by_vendor(vendor_initials_chrome, df_customers)

# Calculate total time to send messages to all customers
total_time = calculate_total_time(customers_edge, customers_chrome)
total_customers = df_customers.shape[0]

# Print customer information for Edge and Chrome browsers
if total_customers > 0:
    print_customers(vendor_initials_edge, customers_edge)
    print_customers(vendor_initials_chrome, customers_chrome)

# Show confirmation dialog and proceed based on user input
if show_confirmation_dialog(total_customers, total_time):
    send_messages_to_customers(customers_edge, EDGE_PATH)
    send_messages_to_customers(customers_chrome, CHROME_PATH)
else:
    print("Program canceled by user.")

show_end_dialog()
