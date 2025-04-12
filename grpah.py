import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

def bilinear_transform(numerator, denominator, sampling_freq):
    """
    Apply bilinear transformation to convert an analog filter to a digital filter.
    
    :param numerator: Coefficients of the numerator of the analog filter transfer function
    :param denominator: Coefficients of the denominator of the analog filter transfer function
    :param sampling_freq: Sampling frequency in Hz
    :return: Numerator and denominator coefficients of the digital filter
    """
    num_z, den_z = signal.bilinear(numerator, denominator, fs=sampling_freq)
    return num_z, den_z

def plot_frequency_response(num, den, fs):
    """Plots the frequency response of the digital filter."""
    w, h = signal.freqz(num, den, fs=fs)
    plt.figure()
    plt.semilogx(w, 20 * np.log10(abs(h)))
    plt.title("Frequency Response of the Digital Filter")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude [dB]")
    plt.grid()
    plt.show()

# Example usage
if __name__ == "__main__":
    analog_num = [1]
    analog_den = [1, 1]  # First-order low-pass filter (s + 1)
    fs = 10  # Sampling frequency in Hz
    
    digital_num, digital_den = bilinear_transform(analog_num, analog_den, fs)
    
    print("Digital filter numerator coefficients:", digital_num)
    print("Digital filter denominator coefficients:", digital_den)
    
    plot_frequency_response(digital_num, digital_den, fs)
