import React from 'react';
import { SimpleGrid } from '@chakra-ui/react';
import { type GymClass } from '../../types';
import ClassCard from './ClassCard';


interface ClassListProps {
  classes: GymClass[];
  onClassSelect: (classId: string) => void; // Prop para notificar la selección
}

const ClassList: React.FC<ClassListProps> = ({ classes , onClassSelect}) => {
  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={8} p={5}>
      {classes.map((classItem) => (
        <ClassCard key={classItem.id} gymClass={classItem} onClick={() => onClassSelect(classItem.id)}/>
      ))}
    </SimpleGrid>
  );
};

export default ClassList;