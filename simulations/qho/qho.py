import numpy as np
from typing import List
import scipy.integrate as integrate
from scipy.special import hermite
from scipy.special import factorial
from scipy.misc import derivative
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.lines import Line2D
from mpl_toolkits import mplot3d
from mpl_toolkits.mplot3d.art3d import Line3D
from mpl_toolkits.mplot3d.axes3d import Axes3D
import itertools

'''
Code plan and structure:

One-dimensional:
1. Given an arbitrary Hamiltonian H, find the eigenvalues E_n.
2. Estimate the matrix form of the Hamiltonian in a finite-dimensional approximation in the QHO basis.
  a. Determine the numerical solutions to the differential equations H.psi = E_n.psi. (Call it numSolution[n])
  b. Perform functional optimization over the parameter space by finding the set of coefficients,
     [c_0, c_1, ..., c_n] such that the value

     QHOBasisApprox = numSolution[n](x) - sum([c[n] * hilbert.eigenbasis(n, x) for n in range(hilbert.dim)])

     assumes its minimum value.
  c. Take the basis approximation and form an approximation of the Hamiltonian,

     H = np.empty(2*[len(numSolution])
     for i, j in itertools.product(range(hilbert.dim), range(hilbert.dim)):
         H[i][j] = lambda x: np.conj(QHOBasisApprox[i](x)) * QHOBasisApprox[j](x)
  d. Set the unitary time operator to be

     U = lambda x, t: np.exp(-i/hbar * H(x) * t)
  e. Evolve the wave function to be
     psi = U(x, t) * initWaveFunc
3. 


Three-dimensional:
'''


class FunctionSampler:
    # Secret occult tricks to make computing our basis functions cheap.

    def __init__(self, f, minX, maxX, numSamples):
        self.minX = minX
        self.maxX = maxX
        self.range = maxX - minX
        self.numSamples = numSamples

        self.domain = np.linspace(minX, maxX, numSamples)
        self.image = [f(x) for x in self.domain]

    def __call__(self, x):
        x = min(max(x, self.minX), self.maxX - 1)
        x -= self.minX
        x = round(x * (self.numSamples / self.range))

        return self.image[int(x)]


class HilbertSpace:

    def __init__(self, dim, basis='QHO', hamiltonianPotential=None):
        self.dim = dim

        if hamiltonianPotential is not None:
            self.V = hamiltonianPotential

        if basis == 'QHO':
            self.QHOBasis = lambda n, x: (1 / np.sqrt(2 ** n * factorial(n)) * np.pi ** (1 / 4)) * np.exp(
                -x ** 2 / 2) * hermite(n)(x)

            QHOBasisApprox = []

            for n in range(self.dim):
                QHOBasisApprox.append(FunctionSampler(lambda x: self.QHOBasis(n, x), -15, 15, 2000))

            self.QHOBasis = lambda n, x: QHOBasisApprox[n](x)

            self.eigenbasis = self.QHOBasis
            self.eigenvalues = lambda n: 1 / 2 + n


class WaveFunction:

    def __init__(self, hilbertSpace, initWaveFunc=None, coeff=None):
        self.hilbert = hilbertSpace

        if coeff != None:
            self.coeff = coeff

        else:
            self.evaluate = lambda x: initWaveFunc(x)
            self.coeff = self.orthogonalBasisProjection(initWaveFunc)

        evaluate = lambda x, t: sum(
            [self.coeff[n] * self.hilbert.eigenbasis(n, x) * self.phaseFactor(n, t) for n in range(self.hilbert.dim)])

        normF = self.normalize(lambda x: evaluate(x, 0))

        self.evaluate = lambda x, t: evaluate(x, t) / normF

    def phaseFactor(self, n, t):
        return np.exp(-1j * self.hilbert.eigenvalues(n) * t)

    def normalize(self, waveFunc):
        return np.sqrt(integrate.quad(lambda x: np.absolute(waveFunc(x)) ** 2, -np.inf, np.inf)[0])

    def orthogonalBasisProjection(self, waveFunc):
        coeff = []
        for n in range(hs.dim):
            coeff.append(
                integrate.quad(lambda x: np.conj(self.hilbert.eigenbasis(n, x)) * waveFunc(x), -np.inf, np.inf)[0])

        return coeff


class Plotter:

    def __init__(self):
        pass

    def plotWaveFunction2d(self, waveFunction, samples=50, frames=250, timeFactor=1, saveName=None):

        fig = plt.figure()
        ax1 = plt.axes(xlim=(-5, 5), ylim=(-1, 1))
        line, = ax1.plot([], [], lw=2)
        plt.xlabel('$x$')
        plt.ylabel('$\psi(x)$')
        plt.xticks([], [])
        plt.yticks([], [])

        plotlays, plotcols = [2], ["blue", "red", "green"]
        lines = []
        for index in range(3):
            lobj = ax1.plot([], [], lw=2, color=plotcols[index])[0]
            lines.append(lobj)

        def init():
            for line in lines:
                line.set_data([], [])
            return lines

        def animate(i):
            posValues = np.linspace(-5, 5, samples)
            amplitudeValues = [waveFunction.evaluate(x, timeFactor * i / 50) for x in posValues]

            reValues = np.real(amplitudeValues)
            imValues = np.imag(amplitudeValues)
            probValues = np.absolute(amplitudeValues) ** 2

            ylist = [reValues, imValues, probValues]

            for lnum, line in enumerate(lines):
                line.set_data(posValues, ylist[lnum])

            return lines

        anim = animation.FuncAnimation(fig, animate, init_func=init, frames=frames, interval=10, blit=True)

        if saveName != None:
            anim.save(saveName + '.mp4', fps=30, extra_args=['-vcodec', 'libx264'])

        plt.show()

    def plotWaveFunction3d(self, waveFunction: WaveFunction, samples=50, frames=250, timeFactor=1, saveName=None):
        # Setup Plot
        fig = plt.figure()
        ax1 = fig.add_axes([0, 0, 1, 1], projection='3d')
        ax1.set_xlabel('$x$')
        ax1.set_ylabel('Im$(\psi)$')
        ax1.set_zlabel('Re$(\psi)$')

        ax1.set_xlim((-5, 5))
        ax1.set_ylim((-1, 1))
        ax1.set_zlim((-1, 1))

        ax1.set_xticks([])
        ax1.set_yticks([])
        ax1.set_zticks([])

        plotlays, plotcols = [2], ["blue", "red", "green"]

        lines: List[Line3D] = []
        pts = []

        for index in [0, 1]:
            lobj = ax1.plot([], [], [], lw=2, color=plotcols[index])[0]
            pobj = ax1.plot([], [], [], lw=2, color=plotcols[index])[0]
            lines.append(lobj)
            pts.append(pobj)

        def init():
            for line, pt in zip(lines, pts):
                line.set_data_3d(np.array([]), np.array([]), np.array([]))

            return lines + pts

        def animate(i):
            # elev, azim = frame_path(i)
            # ax1.view_init(elev, azim)

            # Positions along x axis
            posValues = np.linspace(-5, 5, samples)
            # Complex Amplitude of wave function on x axis after time t
            amplitudeValues = [waveFunction.evaluate(x, timeFactor * i / 50) for x in posValues]
            # Real part of wave function
            reValues = np.real(amplitudeValues)
            # Imaginary part of wave function
            imValues = np.imag(amplitudeValues)
            # Probability amplitude
            probValues = np.absolute(amplitudeValues) ** 2

            ylist = [(imValues, reValues), (0, probValues)]

            for n, line in enumerate(lines):
                line.set_data(posValues, ylist[n][0])
                line.set_3d_properties(ylist[n][1])

            fig.canvas.draw()
            return lines

        anim = animation.FuncAnimation(fig, animate, init_func=init, frames=frames, interval=10, blit=True)

        if saveName is not None:
            anim.save(saveName + '.gif', fps=30)

        plt.show()


p = Plotter()
hs = HilbertSpace(dim=2, hamiltonianPotential=lambda x: 1 / 2 * x ** 2, basis='QHO')
psi = WaveFunction(hs, coeff=[1, 1])

p.plotWaveFunction3d(psi, samples=300, frames=200, timeFactor=2, saveName="qho")
