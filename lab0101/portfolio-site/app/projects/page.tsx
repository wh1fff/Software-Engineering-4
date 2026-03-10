import ProjectCard from '../components/ProjectCard'

// TODO: Создайте массив с данными о проектах
interface Project {
  title: string;
  description: string;
  technologies: string[];
  link: string;
};

const projects: Project[] = [
  {
    title: 'Рекламаркет',
    description: 'Полнофункциональный интернет-магазин',
    technologies: ['Next.js', 'TypeScript', '1C:Bitrix', 'MySQL'],
    link: 'https://stvprint.ru'
  },
  // TODO: Добавьте еще минимум 2 проекта
  {
    title: 'Рекламаркет-авто',
    description: 'Полнофункциональный интернет-магазин со связью с менеджером',
    technologies: ['Next.js', 'TypeScript', 'Bitrix24'],
    link: 'https://auto.stvprint.ru'
  },
  {
    title: 'Корпоративный сайт',
    description: 'Корпоративный сайт Рекламаркет',
    technologies: ['Next.js', 'TypeScript', 'Tailwind CSS', 'Prisma', 'PostgreSQL', 'WordPress'],
    link: 'corp.stvprint.ru'
  }
]

export default function ProjectsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Мои проекты</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* TODO: Используйте компонент ProjectCard для отображения проектов */}
        {projects.map((projects, index) => (
          <ProjectCard
            key = {index}
            title = {projects.title}
            description = {projects.description}
            technologies = {projects.technologies}
            link = {projects.link}
            
          />
        ))
        }
        
      </div>
    </div>
  )
}