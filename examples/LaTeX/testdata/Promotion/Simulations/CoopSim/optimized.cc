// optimized.cc: c++ implementation of some strategies

#include <stdlib.h>
#include "optimized.h"

#define random() (double(rand())/RAND_MAX)


int PrisonersDilemma::noiseFilter(int move) {
        if random() < this->noise {
            if (move == 0) return 1; else return 0;
        } else return move;
}

PrisonersDilemma::PrisonersDilemma(CPPStrategy *playerA, CPPStrategy *playerB, 
                                   int T, int R, int P, int S,
                                   int samples, int noise, 
                                   int maxRounds = MAX_ROUNDS) {
        this->playerA = playerA;  
        this->playerB = playerB;
        this->T = T;  this->R = R;  this->P = P;  this->S = S;
        payoffs[0][0][0] = P;  payoffs[0][0][1] = P;
	payoffs[0][1][0] = T;  payoffs[0][1][1] = S;
        payoffs[1][0][0] = S;  payoffs[1][0][1] = T;
        payoffs[1][1][0] = R;  payoffs[1][1][1] = R;
        this->samples = samples;  
        this->noise = noise;
        this->maxRounds = maxRounds;  
        round = 0;
        movesA = new int[maxRounds];  
        movesB = new int[maxRounds];
        resultA = 0.0;  
        resultB = 0.0;
}

PrisonersDilemma::~PrisonersDilemma() {
        delete movesA;
        delete movesB;
}

void PrisonersDilemma::reset(CPPStrategy *playerA, CPPStrategy *playerB) {
        this->playerA = playerA;  
        this->playerB = playerB;
        round = 0;
        resultA = 0.0;  
        resultB = 0.0;
}

void PrisonersDilemma::play() {
        int sumA, sumB, samples;
        int A, B;
	double div;
	
        if (round > 0) return;	// only play the match once!
        if (noise != 0.0 || playerA->randomizing() ||
            playerB->randomizing()) samples = this->samples;
        else samples = 1;
	sumA = 0; sumB = 0;
        for (int x = 0; x < samples; x++) {
	        A = noiseFilter(playerA->firstMove());
	        B = noiseFilter(playerB->firstMove());
		movesA[0] = A;
		movesB[0] = B;
		sumA += payoffs[A][B][0];
                sumB += payoffs[A][B][1];

		for (int r=1; r < maxRounds; r++) {
	                A = noiseFilter(playerA->nextMove(r, movesA, movesB));
		        B = noiseFilter(playerB->nextMove(r, movesB, movesA));
                        movesA[r] = A;
                        movesB[r] = B;
			sumA += payoffs[A][B][0];
			sumB += payoffs[A][B][1];
		}
	}
        div = (double) (samples * maxRounds);
	resultA = (double)sumA / div;
	resultB = (double)sumB / div; 
}
