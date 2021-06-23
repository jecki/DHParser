// optimized.h: c++ implemented strategies and match functions to increase
//              the speed of the simulation

#define MAX_ROUNDS = 200
#define NUM_SAMPLES = 10

class PrisonersDilemma;	

class CPPStrategy {
	public:	
		virtual bool randomizing() { return false; }
		virtual int firstMove() =0;
		virtual int nextMove(int round, int myMoves[], int opMoves[])=0;
}

class PrisonersDilemma {
	protected:
                int payoffs[2][2][2];
		int noiseFilter(int move);
	public:
		CPPStrategy	*playerA, *playerB;
		int 		T, R, P, S;
		int 		samples;
		double		noise;
		int 		round, maxRounds;
		int		*movesA, *movesB;
		double          resultA, resultB;
	
		PrisonersDilemma(CPPStrategy *playerA, CPPStrategy *playerB, 
				 int T, int R, int P, int S,
				 int noise, int samples = NUM_SAMPLES,
				 int maxRounds = MAX_ROUNDS);
	
		~PrisonersDilemma();
	
		void reset(CPPStrategy *playerA, CPPStrategy *playerB);
		void play();
}
