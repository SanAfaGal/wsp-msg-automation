import os
import subprocess as sb
import time
from tkinter import messagebox
from urllib.parse import quote

import pyautogui as pg
from decouple import config
from pandas import DataFrame
from pywhatkit.core import core, exceptions

from data import get_info_of_customers, filter_data_by_vendor

WSP_SAG = config('BRAVE_PATH')
WSP_BGL = config('EDGE_PATH')

WAIT_TIME_PER_CUSTOMER: int = 15  # Time to wait before sending the message
CLOSE_TAB_WAIT_TIME: int = 2  # Time to wait before closing the tab

IDX_DAY_CUST = '1'
MSG_DAY_CUST = 'Mañana empieza'

VEND_INI_EDGE = 'BGL'
VEND_INI_CHROME = 'SAG'


def log_sent_message(_time: time.struct_time, customer: str, phone_number: str, message: str) -> None:
    """
    Logs the message information after it is sent.

    Parameters:
        _time (time.struct_time): The time at which the message was sent.
        customer (str): The name of the customer.
        phone_number (str): The phone number to which the message was sent.
        message (str): The content of the message.

    Returns:
        None
    """

    folder_path = "logs"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, f'{_time.tm_mday}_{_time.tm_mon}_{_time.tm_year}.txt')

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(
            f"Time: {_time.tm_hour}:{_time.tm_min}:{_time.tm_sec}\n"
            f"Customer: {customer}\n"
            f"Phone Number: {phone_number}\n"
            f"Message: {message}"
        )
        file.write("\n--------------------\n")
        file.close()


def send_wsp_msg(
        customer: dict,
        close_tab_after_send: bool = False,
        browser_path: str = None
) -> None:
    """
    Send WhatsApp message instantly.

    Args:
        customer (dict): Info like name, phone and message about the customer
        close_tab_after_send (bool): Whether to close the browser tab after sending the message, default is False.
        browser_path (str): Path to the browser executable, default is EDGE.

    Raises:
        exceptions.CountryCodeException: If country code is missing in the phone number.
    """

    if not core.check_number(number=customer['TELEFONO']):
        raise exceptions.CountryCodeException("Country Code Missing in Phone Number!")

    # Construct the URL for sending a WhatsApp message using the provided phone number and message content
    url = f"https://web.whatsapp.com/send?phone={customer['TELEFONO']}&text={quote(customer['MENSAJE'])}"
    # Open the specified browser with the constructed URL
    sb.Popen([browser_path, url])
    # Wait for 5 seconds to ensure the WhatsApp Web page is fully loaded
    time.sleep(5)
    # Click at the center of the screen to focus on the message input area in the WhatsApp Web interface
    pg.click(core.WIDTH / 2, core.HEIGHT / 2)
    # Wait for the specified time (minus 5 seconds) before sending the message
    time.sleep(WAIT_TIME_PER_CUSTOMER - 5)
    # Simulate pressing the 'Enter' key to send the message
    # pg.press("enter")
    # Log the sent message along with the current timestamp, receiver's phone number, and message content
    log_sent_message(_time=time.localtime(), customer=customer['CLIENTE'], phone_number=customer['TELEFONO'],
                     message=customer['MENSAJE'])

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
        send_wsp_msg(customer, close_tab_after_send=True,
                     browser_path=browser)
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


def save_info_as_csv(df: DataFrame) -> None:
    """
        Saves a DataFrame to a CSV file.

        Parameters:
            df (DataFrame): The DataFrame to be saved as a CSV file.

        Returns:
            None
        """

    _time = time.localtime()

    folder_path = "csv"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, f'{_time.tm_mday}_{_time.tm_mon}_{_time.tm_year}.csv')

    df.to_csv(file_path)


def print_customers(vendor: str, dict_customer: list[dict]):
    """
    Print customer information for a specific vendor.

    Args:
    vendor (str): The initials of the vendor.
    dict_customer (list[dict]): A list of dictionaries containing customer information.

    Returns:
    None
    """

    if len(dict_customer) > 0:
        print(f"VENDEDOR: {vendor}".center(17, '*'))

        for i, customer in enumerate(dict_customer, start=1):
            print(f"{i}) CLIENTE: {customer['CLIENTE']} - MENSAJE: {customer['MENSAJE']}")

        print()


# >>>>>>>>>>   MAIN   <<<<<<<<<< #

df_customers = get_info_of_customers(IDX_DAY_CUST, MSG_DAY_CUST)
save_info_as_csv(df_customers)

customers_bgl = filter_data_by_vendor(VEND_INI_EDGE, df_customers)
customers_sag = filter_data_by_vendor(VEND_INI_CHROME, df_customers)

total_time = calculate_total_time(customers_bgl, customers_sag)
total_customers = df_customers.shape[0]

print_customers(VEND_INI_EDGE, customers_bgl)
print_customers(VEND_INI_CHROME, customers_sag)

if show_confirmation_dialog(total_customers, total_time):
    send_messages_to_customers(customers_bgl, WSP_BGL)
    send_messages_to_customers(customers_sag, WSP_SAG)
else:
    print("Program canceled by user.")

show_end_dialog()

# >>>>>>>>>>   END   <<<<<<<<<< #
