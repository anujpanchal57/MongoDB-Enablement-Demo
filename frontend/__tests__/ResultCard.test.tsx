import { render, screen } from '@testing-library/react';
import ResultCard from '@/components/ResultCard';
import type { MovieHit } from '@/lib/types';

const baseHit: MovieHit = {
  id: '1',
  title: 'The Godfather',
  year: 1972,
  plot: 'The aging patriarch of an organized crime dynasty transfers control to his son.',
  genres: ['Crime', 'Drama'],
  cast: ['Marlon Brando'],
  imdb_rating: 9.2,
};

describe('ResultCard', () => {
  it('renders title, year and rank', () => {
    render(<ResultCard hit={baseHit} rank={1} accent="#00684A" />);
    expect(screen.getByText('The Godfather')).toBeInTheDocument();
    expect(screen.getByText(/1972/)).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('shows genres and rating', () => {
    render(<ResultCard hit={baseHit} rank={2} accent="#00684A" />);
    expect(screen.getByText('Crime')).toBeInTheDocument();
    expect(screen.getByText(/9\.2/)).toBeInTheDocument();
  });

  it('shows hybrid ranking transparency when ranks are present', () => {
    const hybridHit: MovieHit = {
      ...baseHit,
      fulltext_rank: 3,
      vector_rank: 1,
      fused_score: 0.0312,
    };
    render(<ResultCard hit={hybridHit} rank={1} accent="#5E0C9E" />);
    expect(screen.getByText(/text #3/)).toBeInTheDocument();
    expect(screen.getByText(/vector #1/)).toBeInTheDocument();
    expect(screen.getByText(/RRF 0.0312/)).toBeInTheDocument();
  });
});
