CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(255) NOT NULL,
  correo VARCHAR(255) NOT NULL UNIQUE,
  contrasena VARCHAR(255) NOT NULL,
  area_especialidad VARCHAR(255) NULL,
  tipo VARCHAR(30) NOT NULL DEFAULT 'candidato'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reclutadores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NOT NULL UNIQUE,
  area_especialidad VARCHAR(255) NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  correo VARCHAR(255) NOT NULL,
  telefono VARCHAR(255) NULL,
  CONSTRAINT fk_reclutador_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS candidatos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL UNIQUE,
  cv_url VARCHAR(1024) NULL,
  linkedin VARCHAR(1024) NULL,
  portafolio VARCHAR(1024) NULL,
  CONSTRAINT fk_candidato_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS vacantes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(255) NOT NULL,
  descripcion TEXT NOT NULL,
  requisitos TEXT NULL,
  ubicacion VARCHAR(255) NULL,
  modalidad VARCHAR(100) NULL,
  salario_min DECIMAL(12,2) NULL,
  salario_max DECIMAL(12,2) NULL,
  estado VARCHAR(30) NOT NULL DEFAULT 'activa',
  id_reclutador INT NOT NULL,
  fecha_publicacion DATETIME NULL,
  entrevista JSON NULL,
  datos JSON NULL,
  CONSTRAINT fk_vacante_reclutador FOREIGN KEY (id_reclutador) REFERENCES reclutadores(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS postulaciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_vacante INT NOT NULL,
  id_candidato INT NOT NULL,
  fecha_postulacion DATETIME NOT NULL,
  estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
  UNIQUE KEY uq_postulacion (id_vacante, id_candidato),
  CONSTRAINT fk_postulacion_vacante FOREIGN KEY (id_vacante) REFERENCES vacantes(id) ON DELETE CASCADE,
  CONSTRAINT fk_postulacion_candidato FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS modelos_ia (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS evaluaciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_postulacion INT NOT NULL,
  id_modelo INT NOT NULL,
  puntaje INT NOT NULL,
  observacion TEXT NULL,
  nivel VARCHAR(30) NOT NULL,
  datos JSON NULL,
  fecha_evaluacion DATETIME NOT NULL,
  CONSTRAINT fk_evaluacion_postulacion FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id) ON DELETE CASCADE,
  CONSTRAINT fk_evaluacion_modelo FOREIGN KEY (id_modelo) REFERENCES modelos_ia(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
